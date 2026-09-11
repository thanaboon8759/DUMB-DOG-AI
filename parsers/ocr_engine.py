import logging
from pathlib import Path
from typing import Union
import urllib.request

logger = logging.getLogger(__name__)

try:
    from typhoon_ocr import ocr_document
    TYPHOON_AVAILABLE = True
except ImportError:
    TYPHOON_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


def check_ollama_running() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/", timeout=2)
        return True
    except Exception:
        return False


def _fallback_paddleocr(file_path: Union[str, Path]) -> str:
    if not PADDLE_AVAILABLE:
        logger.warning("PaddleOCR is not available.")
        return ""
    
    logger.info(f"Using PaddleOCR fallback for {file_path}")
    try:
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(str(file_path), cls=True)
        markdown_lines = []
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                markdown_lines.append(line[1][0])
        return "\n\n".join(markdown_lines)
    except Exception as e:
        logger.error(f"Error parsing with PaddleOCR: {e}")
        return ""


def _fallback_pypdf(file_path: Union[str, Path]) -> str:
    if not PYPDF_AVAILABLE:
        logger.warning("pypdf is not available for OCR fallback.")
        return ""
    
    logger.info(f"Using pypdf fallback for {file_path}")
    if Path(file_path).suffix.lower() != ".pdf":
        logger.error("pypdf fallback only supports PDF files.")
        return ""
        
    try:
        reader = PdfReader(str(file_path))
        markdown_lines = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                markdown_lines.append(text)
        return "\n\n".join(markdown_lines)
    except Exception as e:
        logger.error(f"Error parsing PDF with pypdf: {e}")
        return ""


def extract_with_ocr(file_path: Union[str, Path]) -> str:
    """
    Extracts text from PDF or image files using OCR.
    Tries Typhoon OCR first, then PaddleOCR, then pypdf.
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error(f"File not found: {file_path}")
        return ""

    if TYPHOON_AVAILABLE:
        if check_ollama_running():
            try:
                logger.info(f"Using Typhoon OCR for {file_path}")
                markdown = ocr_document(
                    str(file_path), 
                    base_url='http://localhost:11434/v1', 
                    api_key='ollama', 
                    model='scb10x/typhoon-ocr-3b'
                )
                return markdown
            except Exception as e:
                logger.error(f"Typhoon OCR failed: {e}. Attempting fallback.")
        else:
            logger.warning("Ollama is not running. Skipping Typhoon OCR.")
    
    # Fallback to PaddleOCR
    text = _fallback_paddleocr(file_path)
    if text:
        return text
        
    # Last resort fallback to pypdf
    return _fallback_pypdf(file_path)
