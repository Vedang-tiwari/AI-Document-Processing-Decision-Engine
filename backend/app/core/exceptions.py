from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


class DocumentNotFoundException(AppException):
    def __init__(self, document_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="DOCUMENT_NOT_FOUND",
            message=f"The requested document '{document_id}' does not exist.",
        )


class InvalidStateTransitionException(AppException):
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot transition document from status '{current_status}' to '{target_status}'.",
        )


class DuplicateDocumentException(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="DUPLICATE_DOCUMENT",
            message=message,
            details=details,
        )


class FileValidationException(AppException):
    def __init__(self, message: str, code: str = "INVALID_FILE"):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE if "format" in message.lower() else status.HTTP_400_BAD_REQUEST,
            code=code,
            message=message,
        )


class FileTooLargeException(AppException):
    def __init__(self, max_mb: int):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            code="FILE_TOO_LARGE",
            message=f"File exceeds the maximum allowed size of {max_mb} MB.",
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message=message,
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Insufficient permissions to perform this operation"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
        )
