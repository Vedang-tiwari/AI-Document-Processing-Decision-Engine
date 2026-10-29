import io
from typing import Optional
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class OCRService:
    @staticmethod
    def extract_text_from_image_bytes(image_bytes: bytes) -> str:
        """
        Run OCR on an image byte buffer using pytesseract with fallback.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if PYTESSERACT_AVAILABLE:
                try:
                    text = pytesseract.image_to_string(
                        image,
                        lang=settings.OCR_LANGUAGE,
                        timeout=settings.OCR_TIMEOUT_SECONDS,
                    )
                    return text.strip()
                except Exception as t_err:
                    logger.warning(f"pytesseract execution error: {t_err}. Falling back to image OCR parser.")
            
            # If tesseract command is missing or failed on host, return note
            return f"[OCR fallback: image size {image.size}, format {image.format}]"
        except Exception as e:
            logger.error(f"Failed to process image for OCR: {e}")
            return ""

    @staticmethod
    def is_ocr_available() -> bool:
        if not PYTESSERACT_AVAILABLE:
            return False
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
