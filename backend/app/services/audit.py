from typing import Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models.models import AuditEvent
from backend.app.core.logging import logger


class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        document_id: Optional[str] = None,
        actor_type: str = "system",
        actor_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record an immutable audit event. Sensitive keys in metadata are automatically sanitized.
        """
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if any(s in k.lower() for s in ["password", "secret", "token", "key", "auth"]):
                    clean_meta[k] = "[REDACTED]"
                else:
                    clean_meta[k] = v

        event = AuditEvent(
            document_id=document_id,
            actor_type=actor_type,
            actor_id=actor_id,
            event_type=event_type,
            metadata_json=clean_meta,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        # Note: caller will commit within transaction
        logger.info(
            f"Audit event '{event_type}' recorded for document '{document_id}' by actor '{actor_type}:{actor_id}'"
        )
        return event
