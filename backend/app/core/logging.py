import logging
import json
import sys
from typing import Any, Dict
from contextvars import ContextVar

# Context variables for correlation IDs
correlation_request_id: ContextVar[str] = ContextVar("correlation_request_id", default="")
correlation_document_id: ContextVar[str] = ContextVar("correlation_document_id", default="")
correlation_run_id: ContextVar[str] = ContextVar("correlation_run_id", default="")


class StructuredJsonFormatter(logging.Formatter):
    """
    Structured JSON formatter ensuring correlation tracking and safe logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        req_id = correlation_request_id.get()
        doc_id = correlation_document_id.get()
        run_id = correlation_run_id.get()

        if req_id:
            log_obj["request_id"] = req_id
        if doc_id:
            log_obj["document_id"] = doc_id
        if run_id:
            log_obj["processing_run_id"] = run_id

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Merge custom attributes if provided in record.extra
        if hasattr(record, "structured_data") and isinstance(record.structured_data, dict):
            # Redact known sensitive fields
            for k, v in record.structured_data.items():
                if any(s in k.lower() for s in ["password", "secret", "token", "key", "auth"]):
                    log_obj[k] = "[REDACTED]"
                else:
                    log_obj[k] = v

        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers = [handler]

    # Silence overly verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


logger = logging.getLogger("document_engine")
