"""
Phase 1: Local File Routing Gateway

Accepts PDF, DOCX, and Image files. Determines whether each file
should be routed to the Docling parser (clean text) or the PaddleOCR
engine (scanned / garbled documents).

Key feature: Thai Garble Test
    Many Thai PDFs produced by older software embed text with detached
    vowel marks (สระลอย) and tone marks, resulting in garbled extraction.
    This module detects that corruption pattern and routes affected files
    to OCR for re-extraction.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from pypdf import PdfReader

from schemas.models import FileType, RouteDecision, RoutingResult

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────

# Supported file extensions mapped to FileType
_EXT_MAP: dict[str, FileType] = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".doc": FileType.DOCX,
    ".png": FileType.IMAGE,
    ".jpg": FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
    ".tiff": FileType.IMAGE,
    ".tif": FileType.IMAGE,
    ".bmp": FileType.IMAGE,
    ".webp": FileType.IMAGE,
}

# Thai Unicode block ranges for garble detection
# Thai consonants: U+0E01 – U+0E2E
_THAI_CONSONANTS = set(range(0x0E01, 0x0E2F))

# Thai vowels that MUST follow a consonant (above/below/after marks)
_THAI_COMBINING_MARKS = (
    set(range(0x0E31, 0x0E3B))  # สระบน / สระล่าง (◌ั ◌ิ ◌ี ◌ึ ◌ื ◌ุ ◌ู ◌ฺ etc.)
    | set(range(0x0E47, 0x0E4F))  # วรรณยุกต์ + การันต์ (◌็ ◌่ ◌้ ◌๊ ◌๋ ◌์ ◌ํ ◌๎)
)

# Characters that suggest encoding corruption
_REPLACEMENT_CHARS = {"\ufffd", "\x00", "\ufffe", "\uffff"}

# Garble test thresholds
_MIN_EXTRACTED_CHARS = 100  # Below this → assume image-based / scan
_GARBLE_SCORE_THRESHOLD = 0.15  # Above this → flag as garbled
_SAMPLE_CHARS = 500  # Number of characters to sample for the garble test


# ── Garble Detection ────────────────────────────────────────────────────


def _compute_garble_score(text: str) -> tuple[float, str]:
    """
    Analyse extracted text for Thai encoding corruption.

    Returns:
        (garble_score, reason)
        garble_score: 0.0 = perfectly clean, 1.0 = fully garbled
        reason: human-readable explanation
    """
    if not text or len(text.strip()) == 0:
        return 1.0, "No text extracted — likely a scanned/image-based document"

    sample = text[:_SAMPLE_CHARS]
    total_chars = len(sample)

    if total_chars == 0:
        return 1.0, "Empty text sample"

    # ── Check 1: Replacement / control characters ────────────────────
    replacement_count = sum(1 for ch in sample if ch in _REPLACEMENT_CHARS)
    replacement_ratio = replacement_count / total_chars

    # ── Check 2: Detached Thai combining marks ───────────────────────
    # A combining mark (vowel above/below, tone mark) appearing at
    # position 0 or after a non-Thai-consonant character is "detached"
    # — a strong signal of garbled encoding.
    detached_count = 0
    thai_mark_count = 0

    for i, ch in enumerate(sample):
        cp = ord(ch)
        if cp in _THAI_COMBINING_MARKS:
            thai_mark_count += 1
            # Check if the preceding character is a Thai consonant
            if i == 0 or ord(sample[i - 1]) not in _THAI_CONSONANTS:
                detached_count += 1

    detached_ratio = (
        detached_count / thai_mark_count if thai_mark_count > 0 else 0.0
    )

    # ── Check 3: Whitespace fragmentation ────────────────────────────
    # Garbled Thai PDFs often insert spaces between every character
    words = sample.split()
    single_char_words = sum(1 for w in words if len(w) == 1)
    fragmentation_ratio = (
        single_char_words / len(words) if words else 0.0
    )

    # ── Composite score (weighted) ───────────────────────────────────
    score = (
        0.40 * detached_ratio
        + 0.35 * replacement_ratio
        + 0.25 * fragmentation_ratio
    )
    score = min(score, 1.0)

    # Build reason string
    reasons: list[str] = []
    if detached_ratio > 0.1:
        reasons.append(
            f"Detached Thai marks: {detached_count}/{thai_mark_count} "
            f"({detached_ratio:.0%})"
        )
    if replacement_ratio > 0.05:
        reasons.append(
            f"Replacement/control chars: {replacement_count}/{total_chars} "
            f"({replacement_ratio:.0%})"
        )
    if fragmentation_ratio > 0.3:
        reasons.append(
            f"High fragmentation: {single_char_words}/{len(words)} single-char words "
            f"({fragmentation_ratio:.0%})"
        )

    reason = "; ".join(reasons) if reasons else "Text appears clean"
    return score, reason


# ── PDF Text Extraction ─────────────────────────────────────────────────


def _extract_pdf_text(file_path: str | Path, max_chars: int = _SAMPLE_CHARS) -> str:
    """
    Extract text from a PDF using pypdf.

    Reads pages sequentially until `max_chars` characters are accumulated
    or all pages are exhausted.
    """
    text_parts: list[str] = []
    total_len = 0

    try:
        reader = PdfReader(str(file_path))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                total_len += len(page_text)
            if total_len >= max_chars:
                break
    except Exception as exc:
        logger.warning("pypdf extraction failed for %s: %s", file_path, exc)
        return ""

    return "".join(text_parts)


# ── File Type Detection ─────────────────────────────────────────────────


def detect_file_type(file_path: str | Path) -> FileType:
    """
    Determine the FileType from the file extension.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(file_path).suffix.lower()
    file_type = _EXT_MAP.get(ext)
    if file_type is None:
        supported = ", ".join(sorted(_EXT_MAP.keys()))
        raise ValueError(
            f"Unsupported file extension '{ext}'. Supported: {supported}"
        )
    return file_type


# ── Main Router ─────────────────────────────────────────────────────────


def route_file(file_path: str | Path) -> RoutingResult:
    """
    Route an input file to the appropriate parsing engine.

    Decision logic:
    1. Images → always OCR
    2. DOCX  → always Docling (DOCX is machine-readable by definition)
    3. PDF   → run the Thai Garble Test:
       a. Extract first 500 chars via PyMuPDF
       b. If char count < 100  → OCR (likely a scan)
       c. If garble_score > 0.15 → OCR (encoding corruption detected)
       d. Otherwise → Docling (clean PDF)
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_type = detect_file_type(file_path)

    # ── Images: always OCR ───────────────────────────────────────────
    if file_type == FileType.IMAGE:
        logger.info("Image file detected — routing to OCR: %s", file_path.name)
        return RoutingResult(
            file_path=str(file_path),
            file_type=file_type,
            route=RouteDecision.OCR,
            requires_ocr=True,
            garble_score=1.0,
            extracted_char_count=0,
            extracted_preview="",
            reason="Image file — OCR required",
        )

    # ── DOCX: always Docling ─────────────────────────────────────────
    if file_type == FileType.DOCX:
        logger.info("DOCX file detected — routing to Docling: %s", file_path.name)
        return RoutingResult(
            file_path=str(file_path),
            file_type=file_type,
            route=RouteDecision.DOCLING,
            requires_ocr=False,
            garble_score=0.0,
            extracted_char_count=0,
            extracted_preview="",
            reason="DOCX file — machine-readable, using Docling",
        )

    # ── PDF: run the garble test ─────────────────────────────────────
    logger.info("PDF file detected — running garble test: %s", file_path.name)
    extracted_text = _extract_pdf_text(file_path)
    char_count = len(extracted_text.strip())

    # Sub-threshold character count → scan / image-based PDF
    if char_count < _MIN_EXTRACTED_CHARS:
        logger.info(
            "PDF has only %d chars (< %d) — routing to OCR",
            char_count,
            _MIN_EXTRACTED_CHARS,
        )
        return RoutingResult(
            file_path=str(file_path),
            file_type=file_type,
            route=RouteDecision.OCR,
            requires_ocr=True,
            garble_score=1.0,
            extracted_char_count=char_count,
            extracted_preview=extracted_text[:200],
            reason=(
                f"Insufficient extracted text ({char_count} chars < {_MIN_EXTRACTED_CHARS}) "
                f"— likely a scanned PDF"
            ),
        )

    # Run garble scoring
    garble_score, garble_reason = _compute_garble_score(extracted_text)

    if garble_score > _GARBLE_SCORE_THRESHOLD:
        logger.info(
            "PDF garble score %.2f > %.2f — routing to OCR: %s",
            garble_score,
            _GARBLE_SCORE_THRESHOLD,
            garble_reason,
        )
        return RoutingResult(
            file_path=str(file_path),
            file_type=file_type,
            route=RouteDecision.OCR,
            requires_ocr=True,
            garble_score=garble_score,
            extracted_char_count=char_count,
            extracted_preview=extracted_text[:200],
            reason=f"Thai garble detected (score={garble_score:.2f}): {garble_reason}",
        )

    # Clean PDF → Docling
    logger.info(
        "PDF is clean (garble=%.2f) — routing to Docling: %s",
        garble_score,
        file_path.name,
    )
    return RoutingResult(
        file_path=str(file_path),
        file_type=file_type,
        route=RouteDecision.DOCLING,
        requires_ocr=False,
        garble_score=garble_score,
        extracted_char_count=char_count,
        extracted_preview=extracted_text[:200],
        reason=f"Clean PDF (garble={garble_score:.2f}): {garble_reason}",
    )


# ── Batch Router ────────────────────────────────────────────────────────


def route_files(file_paths: list[str | Path]) -> list[RoutingResult]:
    """Route multiple files and return a list of RoutingResults."""
    results: list[RoutingResult] = []
    for fp in file_paths:
        try:
            result = route_file(fp)
            results.append(result)
        except (FileNotFoundError, ValueError) as exc:
            logger.error("Skipping file %s: %s", fp, exc)
    return results
