import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def _fallback_parse_pdf(file_path: Union[str, Path]) -> str:
    if not PYPDF_AVAILABLE:
        logger.error("pypdf is not available for PDF fallback parsing.")
        return ""
    
    logger.info(f"Using pypdf fallback for {file_path}")
    try:
        reader = PdfReader(str(file_path))
        markdown_lines = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                markdown_lines.append(text)
        return "\n\n".join(markdown_lines)
    except Exception as e:
        logger.error(f"Error parsing PDF with pypdf: {e}")
        return ""


def _fallback_parse_docx(file_path: Union[str, Path]) -> str:
    if not DOCX_AVAILABLE:
        logger.error("python-docx is not available for DOCX fallback parsing.")
        return ""

    logger.info(f"Using python-docx fallback for {file_path}")
    try:
        doc = DocxDocument(str(file_path))
        markdown_lines = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                markdown_lines.append(paragraph.text.strip())
        return "\n\n".join(markdown_lines)
    except Exception as e:
        logger.error(f"Error parsing DOCX with python-docx: {e}")
        return ""


def parse_with_docling(file_path: Union[str, Path]) -> str:
    """
    Parses a PDF or DOCX file to Markdown.
    Uses docling if available, falling back to pypdf or python-docx.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"File not found: {file_path}")
        return ""

    extension = file_path_obj.suffix.lower()

    if DOCLING_AVAILABLE:
        try:
            logger.info(f"Using docling for {file_path}")
            converter = DocumentConverter()
            result = converter.convert(str(file_path))
            markdown = result.document.export_to_markdown()
            return markdown
        except Exception as e:
            logger.error(f"Docling conversion failed: {e}. Attempting fallback.")

    # Fallback
    if extension == ".pdf":
        return _fallback_parse_pdf(file_path)
    elif extension in [".docx", ".doc"]:
        return _fallback_parse_docx(file_path)
    else:
        logger.error(f"Unsupported file format for fallback parsing: {extension}")
        return ""
