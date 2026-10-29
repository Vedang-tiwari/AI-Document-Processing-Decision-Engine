import hashlib
import uuid
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import UploadFile

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    FileValidationException,
    FileTooLargeException,
)
from backend.app.db.models.models import Document
from backend.app.storage.local import get_storage_adapter
from backend.app.services.audit import AuditService
from backend.app.core.logging import logger


SUPPORTED_MIME_TYPES = {
    "application/pdf": [b"%PDF-"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
}


class IngestionService:
    @staticmethod
    def validate_file_content(content: bytes, filename: str) -> str:
        """
        Validate actual file magic bytes and size limits. Returns normalized mime_type.
        """
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeException(settings.MAX_FILE_SIZE_MB)

        if len(content) < 4:
            raise FileValidationException("Uploaded file is empty or corrupted", "EMPTY_FILE")

        detected_mime = None
        for mime, signatures in SUPPORTED_MIME_TYPES.items():
            for sig in signatures:
                if content.startswith(sig):
                    detected_mime = mime
                    break
            if detected_mime:
                break

        if not detected_mime:
            raise FileValidationException(
                "Unsupported file format. Supported formats are PDF, PNG, and JPEG.",
                "UNSUPPORTED_MEDIA_TYPE",
            )

        return detected_mime

    @staticmethod
    def ingest_document(
        db: Session,
        content: bytes,
        filename: str,
        user_id: Optional[str] = None,
        expected_type: Optional[str] = None,
    ) -> Document:
        """
        Ingest, validate, store, and persist document record in queued status.
        """
        mime_type = IngestionService.validate_file_content(content, filename)
        file_hash = hashlib.sha256(content).hexdigest()
        doc_id = str(uuid.uuid4())

        # Determine extension and storage key
        ext = ".pdf" if mime_type == "application/pdf" else (".png" if mime_type == "image/png" else ".jpg")
        storage_key = f"{doc_id}{ext}"

        # Store file safely
        storage = get_storage_adapter()
        storage.save(content, storage_key)

        document = Document(
            id=doc_id,
            original_filename=filename,
            mime_type=mime_type,
            file_size_bytes=len(content),
            file_hash=file_hash,
            storage_key=storage_key,
            document_type=expected_type or "unknown",
            status="queued",
            processing_attempts=0,
            uploaded_by=user_id,
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Record audit event
        AuditService.log_event(
            db=db,
            event_type="document.uploaded",
            document_id=doc_id,
            actor_type="user" if user_id else "system",
            actor_id=user_id,
            metadata={
                "filename": filename,
                "mime_type": mime_type,
                "size_bytes": len(content),
                "file_hash": file_hash,
            },
        )
        db.commit()

        logger.info(f"Document '{doc_id}' successfully ingested and queued.")
        return document
