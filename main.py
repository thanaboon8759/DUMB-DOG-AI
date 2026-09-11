"""
Resume Parsing Pipeline — CLI Entrypoint

Usage:
    python main.py <file1> [file2] [file3] ...
    python main.py --dir <directory>

Examples:
    python main.py resume.pdf
    python main.py resume1.pdf resume2.docx photo.png
    python main.py --dir ./resumes/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from parsers.router import route_file, route_files

# ── Logging Setup ───────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("resume-pipeline")


# ── Hardware Detection ──────────────────────────────────────────────────


def check_hardware() -> dict[str, object]:
    """Detect available hardware (CPU / CUDA GPU) and log findings."""
    hw_info: dict[str, object] = {
        "cuda_available": False,
        "gpu_name": None,
        "gpu_count": 0,
    }

    try:
        import torch

        hw_info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            hw_info["gpu_count"] = torch.cuda.device_count()
            hw_info["gpu_name"] = torch.cuda.get_device_name(0)
            logger.info(
                "🟢 CUDA GPU detected: %s (x%d)",
                hw_info["gpu_name"],
                hw_info["gpu_count"],
            )
        else:
            logger.info("🟡 No CUDA GPU detected — pipeline will run on CPU")
    except ImportError:
        logger.info(
            "🟡 PyTorch not installed — GPU detection skipped, will use CPU"
        )

    return hw_info


# ── File Discovery ──────────────────────────────────────────────────────

_SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc",
    ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp",
}


def discover_files(paths: list[str]) -> list[Path]:
    """
    Resolve CLI arguments into a flat list of supported files.

    Accepts individual file paths or directories (non-recursive).
    """
    files: list[Path] = []
    for p in paths:
        path = Path(p).resolve()
        if path.is_file():
            if path.suffix.lower() in _SUPPORTED_EXTENSIONS:
                files.append(path)
            else:
                logger.warning("Skipping unsupported file: %s", path.name)
        elif path.is_dir():
            dir_files = sorted(
                f
                for f in path.iterdir()
                if f.is_file() and f.suffix.lower() in _SUPPORTED_EXTENSIONS
            )
            logger.info("Found %d supported files in %s", len(dir_files), path)
            files.extend(dir_files)
        else:
            logger.warning("Path not found: %s", p)
    return files


# ── Pretty Printing ─────────────────────────────────────────────────────


def print_routing_table(results: list) -> None:
    """Print a formatted summary table of routing decisions."""
    if not results:
        print("\n  No files were processed.\n")
        return

    # Column widths
    name_w = max(len(Path(r.file_path).name) for r in results)
    name_w = max(name_w, 8)  # minimum "Filename" header

    header = (
        f"  {'Filename':<{name_w}}  │ {'Type':<5} │ {'Route':<7} │ "
        f"{'Garble':>6} │ {'Chars':>5} │ Reason"
    )
    sep = "  " + "─" * (len(header) + 10)

    print(f"\n{sep}")
    print(f"  📋 Routing Results ({len(results)} file(s))")
    print(sep)
    print(header)
    print(sep)

    for r in results:
        name = Path(r.file_path).name
        route_icon = "🔍 OCR" if r.route.value == "ocr" else "📄 Doc"
        print(
            f"  {name:<{name_w}}  │ {r.file_type.value:<5} │ {route_icon:<7} │ "
            f"{r.garble_score:>5.2f} │ {r.extracted_char_count:>5} │ {r.reason}"
        )

    print(f"{sep}\n")


# ── Main ────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entrypoint for the resume parsing pipeline."""
    parser = argparse.ArgumentParser(
        description="AI Resume Parsing Pipeline — Local Routing Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py resume.pdf\n"
            "  python main.py --dir ./resumes/\n"
            "  python main.py file1.pdf file2.docx scan.png\n"
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Input file(s) to process (PDF, DOCX, or image)",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Directory containing resume files to process",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output routing results as JSON",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Run full pipeline: route → parse → LLM extract (requires Ollama)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen2.5:7b",
        help="LLM model for extraction (default: qwen2.5:7b)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Header
    print("\n" + "=" * 60)
    print("  AI Resume Parsing Pipeline")
    print("=" * 60)

    # Hardware check
    hw = check_hardware()

    # Collect file paths
    input_paths: list[str] = list(args.files) if args.files else []
    if args.dir:
        input_paths.append(args.dir)

    if not input_paths:
        print("\n  No input files specified. Use --help for usage.\n")
        sys.exit(1)

    files = discover_files(input_paths)
    if not files:
        print("\n  No supported files found in the provided paths.\n")
        sys.exit(1)

    logger.info("Processing %d file(s)...", len(files))

    # Route all files
    results = route_files(files)

    # Output routing table
    if args.json and not args.extract:
        output = [r.model_dump() for r in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    elif not args.extract:
        print_routing_table(results)

    # Summary
    ocr_count = sum(1 for r in results if r.requires_ocr)
    docling_count = len(results) - ocr_count
    print(f"  Routing: {docling_count} -> Docling, {ocr_count} -> OCR")

    # ── Full pipeline mode ───────────────────────────────────────────
    if args.extract:
        from parsers.docling_parser import parse_with_docling
        from parsers.ocr_engine import extract_with_ocr

        print(f"\n  --- Phase 2: Parsing documents ---")
        parsed_docs: list[tuple[str, str]] = []  # (filename, markdown)

        for r in results:
            fname = Path(r.file_path).name
            if r.requires_ocr:
                logger.info("OCR route: %s", fname)
                md = extract_with_ocr(r.file_path)
            else:
                logger.info("Docling route: %s", fname)
                md = parse_with_docling(r.file_path)

            parsed_docs.append((fname, md))
            chars = len(md)
            print(f"    {fname}: {chars} chars extracted")

        print(f"\n  --- Phase 3: LLM Extraction (model={args.model}) ---")
        try:
            from extraction.llm_local import extract_candidate_profile, OllamaConnectionError
        except ImportError as e:
            print(f"  ERROR: Missing dependency: {e}")
            print("  Install: pip install instructor openai")
            sys.exit(1)

        profiles = []
        for fname, md in parsed_docs:
            if not md.strip():
                print(f"    {fname}: SKIPPED (empty text)")
                continue
            try:
                profile = extract_candidate_profile(md, model=args.model)
                profiles.append((fname, profile))
                print(f"    {fname}: {profile.full_name} | "
                      f"{len(profile.skills)} skills | "
                      f"{len(profile.experience)} exp | "
                      f"{len(profile.education)} edu")
            except OllamaConnectionError:
                print(f"\n  ERROR: Ollama is not running at localhost:11434")
                print("  Start with: ollama serve")
                sys.exit(1)
            except Exception as e:
                print(f"    {fname}: FAILED - {e}")

        # Output extracted profiles
        if profiles:
            print(f"\n  --- Results: {len(profiles)} profiles extracted ---")
            if args.json:
                output = {
                    fname: p.model_dump()
                    for fname, p in profiles
                }
                print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
            else:
                for fname, p in profiles:
                    print(f"\n  [{fname}]")
                    print(f"  Name:  {p.full_name}")
                    print(f"  Email: {p.contact_email}")
                    print(f"  Phone: {p.contact_phone}")
                    print(f"  Skills: {', '.join(p.skills[:10])}{'...' if len(p.skills) > 10 else ''}")
                    for exp in p.experience[:3]:
                        print(f"  Exp:   {exp.role} @ {exp.company} ({exp.start_date} - {exp.end_date})")
                    for edu in p.education:
                        print(f"  Edu:   {edu.degree} {edu.field_of_study} @ {edu.institution}")

    print()


if __name__ == "__main__":
    main()

