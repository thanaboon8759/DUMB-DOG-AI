"""
Phase 1 Verification — Tests for the Routing Gateway.

Creates synthetic test files (clean PDF, garbled Thai PDF, DOCX, image)
and validates that the router makes correct routing decisions.

Usage:
    python -m tests.test_router
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from reportlab.pdfgen import canvas

from parsers.router import (
    _compute_garble_score,
    detect_file_type,
    route_file,
)
from schemas.models import FileType, RouteDecision


def _create_clean_pdf(path: Path, text: str) -> None:
    """Create a simple PDF with clean, machine-readable text."""
    c = canvas.Canvas(str(path))
    c.setFont("Helvetica", 12)
    y = 800
    for line in text.split("\n"):
        c.drawString(72, y, line)
        y -= 15
    c.save()


def _create_minimal_pdf(path: Path) -> None:
    """Create a PDF with almost no extractable text (simulates a scan)."""
    c = canvas.Canvas(str(path))
    c.setFont("Helvetica", 1)
    c.drawString(72, 72, ".")
    c.save()


def _create_dummy_image(path: Path) -> None:
    """Create a minimal PNG file."""
    # Minimal valid 1x1 white PNG (67 bytes)
    import struct
    import zlib

    def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = _png_chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = _png_chunk(b"IEND", b"")
    path.write_bytes(header + ihdr + idat + iend)


def _create_dummy_docx(path: Path) -> None:
    """Create a minimal DOCX file (just a zip with the right extension)."""
    import zipfile
    with zipfile.ZipFile(str(path), "w") as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')


# ── Tests ───────────────────────────────────────────────────────────────


def test_garble_score_clean_english() -> None:
    """Clean English text should have a garble score near 0."""
    text = (
        "John Doe is a software engineer with 5 years of experience "
        "in Python, FastAPI, and React. He graduated from MIT with a "
        "degree in Computer Science. Contact: john@example.com"
    )
    score, reason = _compute_garble_score(text)
    assert score < 0.05, f"Clean English text scored {score:.3f}: {reason}"
    print(f"  ✅ Clean English:  garble={score:.3f} — {reason}")


def test_garble_score_clean_thai() -> None:
    """Clean Thai text with properly attached marks should score low."""
    text = (
        "สมชาย เป็นวิศวกรซอฟต์แวร์ที่มีประสบการณ์ 5 ปี "
        "ในการพัฒนาระบบด้วย Python และ FastAPI เขาจบการศึกษา"
        "จากจุฬาลงกรณ์มหาวิทยาลัย สาขาวิทยาการคอมพิวเตอร์"
    )
    score, reason = _compute_garble_score(text)
    assert score < 0.10, f"Clean Thai text scored {score:.3f}: {reason}"
    print(f"  ✅ Clean Thai:     garble={score:.3f} — {reason}")


def test_garble_score_garbled_thai() -> None:
    """
    Simulated garbled Thai: tone marks and vowels detached from consonants.
    This pattern is common in PDFs exported from older Thai word processors.
    """
    # Detach every combining mark by inserting a space before it
    garbled = "ส ม ช า ย  เ ป็ น วิ ศ ว ก ร ซ อ ฟ ต์ แ ว ร์ " * 5
    score, reason = _compute_garble_score(garbled)
    assert score > 0.15, f"Garbled Thai text scored only {score:.3f}: {reason}"
    print(f"  ✅ Garbled Thai:   garble={score:.3f} — {reason}")


def test_garble_score_empty() -> None:
    """Empty text should score 1.0 (maximum garble)."""
    score, reason = _compute_garble_score("")
    assert score == 1.0, f"Empty text scored {score:.3f}"
    print(f"  ✅ Empty text:     garble={score:.3f} — {reason}")


def test_file_type_detection() -> None:
    """File type detection from extensions."""
    assert detect_file_type("resume.pdf") == FileType.PDF
    assert detect_file_type("cv.docx") == FileType.DOCX
    assert detect_file_type("photo.png") == FileType.IMAGE
    assert detect_file_type("scan.jpg") == FileType.IMAGE
    assert detect_file_type("scan.TIFF") == FileType.IMAGE
    print("  ✅ File type detection: all extensions correctly classified")


def test_routing_clean_pdf() -> None:
    """A clean PDF with plenty of text should route to Docling."""
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "clean_resume.pdf"
        long_text = (
            "John Doe — Senior Software Engineer\n"
            "Experience: 5 years at Google, 3 years at Meta\n"
            "Skills: Python, Go, Kubernetes, Machine Learning\n"
            "Education: M.Sc. Computer Science, Stanford University\n"
        ) * 5  # Make it long enough to pass the 100-char threshold
        _create_clean_pdf(pdf_path, long_text)

        result = route_file(pdf_path)
        assert result.route == RouteDecision.DOCLING, (
            f"Clean PDF routed to {result.route} instead of DOCLING: {result.reason}"
        )
        print(f"  ✅ Clean PDF:      route={result.route.value}, garble={result.garble_score:.3f}")


def test_routing_scan_pdf() -> None:
    """A PDF with minimal text (scan) should route to OCR."""
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "scanned_resume.pdf"
        _create_minimal_pdf(pdf_path)

        result = route_file(pdf_path)
        assert result.route == RouteDecision.OCR, (
            f"Scanned PDF routed to {result.route} instead of OCR: {result.reason}"
        )
        print(f"  ✅ Scanned PDF:    route={result.route.value}, chars={result.extracted_char_count}")


def test_routing_image() -> None:
    """Image files should always route to OCR."""
    with tempfile.TemporaryDirectory() as tmp:
        img_path = Path(tmp) / "resume_scan.png"
        _create_dummy_image(img_path)

        result = route_file(img_path)
        assert result.route == RouteDecision.OCR
        assert result.requires_ocr is True
        print(f"  ✅ Image file:     route={result.route.value}")


def test_routing_docx() -> None:
    """DOCX files should always route to Docling."""
    with tempfile.TemporaryDirectory() as tmp:
        docx_path = Path(tmp) / "resume.docx"
        _create_dummy_docx(docx_path)

        result = route_file(docx_path)
        assert result.route == RouteDecision.DOCLING
        assert result.requires_ocr is False
        print(f"  ✅ DOCX file:      route={result.route.value}")


# ── Runner ──────────────────────────────────────────────────────────────


def run_all_tests() -> None:
    """Execute all Phase 1 verification tests."""
    print("\n" + "=" * 60)
    print("  🧪 Phase 1 Verification — Routing Gateway Tests")
    print("=" * 60 + "\n")

    tests = [
        ("Garble: Clean English", test_garble_score_clean_english),
        ("Garble: Clean Thai", test_garble_score_clean_thai),
        ("Garble: Garbled Thai", test_garble_score_garbled_thai),
        ("Garble: Empty text", test_garble_score_empty),
        ("File type detection", test_file_type_detection),
        ("Route: Clean PDF", test_routing_clean_pdf),
        ("Route: Scanned PDF", test_routing_scan_pdf),
        ("Route: Image file", test_routing_image),
        ("Route: DOCX file", test_routing_docx),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            print(f"  ❌ {name}: {exc}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60 + "\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
