import re
from typing import Dict, Any, List
import fitz  # PyMuPDF
from backend.app.services.ocr import OCRService
from backend.app.core.logging import logger


class ParsedPage:
    def __init__(self, page_number: int, text: str, method: str):
        self.page_number = page_number
        self.text = text
        self.method = method  # "native" or "ocr"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "method": self.method,
        }


class ParsedDocument:
    def __init__(self, full_text: str, pages: List[ParsedPage], metadata: Dict[str, Any]):
        self.full_text = full_text
        self.pages = pages
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_text": self.full_text,
            "pages": [p.to_dict() for p in self.pages],
            "metadata": self.metadata,
        }


class DocumentParserService:
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize excessive whitespace and common OCR/PDF artifacts.
        """
        if not text:
            return ""
        # Replace non-breaking spaces
        text = text.replace("\u00a0", " ")
        # Replace multiple spaces with a single space
        text = re.sub(r"[ \t]+", " ", text)
        # Replace more than two newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def parse(cls, content: bytes, mime_type: str) -> ParsedDocument:
        """
        Extract text page-by-page from PDF or image documents.
        """
        pages: List[ParsedPage] = []

        if mime_type == "application/pdf":
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                for page_idx in range(len(doc)):
                    page_num = page_idx + 1
                    page = doc[page_idx]
                    native_text = page.get_text("text").strip()

                    # If page has usable native text (> 20 chars), use native
                    if len(native_text) >= 20:
                        pages.append(ParsedPage(page_num, cls.normalize_text(native_text), "native"))
                    else:
                        # Fallback to OCR for scanned or empty-text pages
                        logger.info(f"Page {page_num} has insufficient native text ({len(native_text)} chars). Running OCR.")
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        ocr_text = OCRService.extract_text_from_image_bytes(img_bytes)
                        text = cls.normalize_text(ocr_text or native_text)
                        pages.append(ParsedPage(page_num, text, "ocr"))
                doc.close()
            except Exception as e:
                logger.error(f"Error parsing PDF document: {e}")
                pages.append(ParsedPage(1, "", "failed"))

        elif mime_type in ["image/png", "image/jpeg"]:
            ocr_text = OCRService.extract_text_from_image_bytes(content)
            pages.append(ParsedPage(1, cls.normalize_text(ocr_text), "ocr"))
        else:
            pages.append(ParsedPage(1, "", "unsupported"))

        full_text = "\n\n--- Page Break ---\n\n".join(
            p.text for p in pages if p.text
        )

        metadata = {
            "page_count": len(pages),
            "extraction_methods": list({p.method for p in pages}),
            "character_count": len(full_text),
        }

        return ParsedDocument(full_text=full_text, pages=pages, metadata=metadata)
