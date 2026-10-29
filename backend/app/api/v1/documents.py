from typing import Optional, List
from datetime import datetime
import io
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.models import Document, ExtractionResult, ProcessingRun
from backend.app.core.security import get_current_user, CurrentUser, require_role
from backend.app.core.exceptions import DocumentNotFoundException, AppException
from backend.app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentListItem,
    DocumentDetailResponse,
    DocumentResultResponse,
    RetryResponse,
)
from backend.app.services.ingestion import IngestionService
from backend.app.storage.local import get_storage_adapter
from backend.app.tasks.document_tasks import dispatch_document_processing

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DocumentUploadResponse,
    summary="Upload a business document for asynchronous processing",
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    doc = IngestionService.ingest_document(
        db=db,
        content=content,
        filename=file.filename or "upload.pdf",
        user_id=current_user.id,
        expected_type=document_type,
    )

    # Dispatch asynchronous background task
    dispatch_document_processing(doc.id)

    return DocumentUploadResponse(
        document_id=doc.id,
        status="queued",
        message="Document accepted for processing.",
    )


@router.get("", response_model=DocumentListResponse, summary="List documents with pagination and filtering")
def list_documents(
    status: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    created_from: Optional[datetime] = Query(None),
    created_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if created_from:
        query = query.filter(Document.created_at >= created_from)
    if created_to:
        query = query.filter(Document.created_at <= created_to)

    total = query.count()
    docs = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for d in docs:
        latest_ext = (
            db.query(ExtractionResult)
            .filter(ExtractionResult.document_id == d.id)
            .order_by(ExtractionResult.created_at.desc())
            .first()
        )
        conf_score = None
        supplier_name = None
        total_amount = None
        if latest_ext:
            conf_data = latest_ext.confidence_data or {}
            conf_score = conf_data.get("document_score")
            ext_data = latest_ext.extracted_data or {}
            supplier_name = (ext_data.get("supplier") or {}).get("name")
            total_amount = str(ext_data.get("total_amount", "")) or None

        items.append(
            DocumentListItem(
                id=d.id,
                original_filename=d.original_filename,
                mime_type=d.mime_type,
                file_size_bytes=d.file_size_bytes,
                document_type=d.document_type,
                status=d.status,
                decision_outcome=d.decision_outcome,
                processing_attempts=d.processing_attempts,
                uploaded_by=d.uploaded_by,
                created_at=d.created_at,
                completed_at=d.completed_at,
                confidence_score=conf_score,
                supplier_name=supplier_name,
                total_amount=total_amount,
            )
        )

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get document metadata and status")
def get_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundException(document_id)

    latest_ext = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.document_id == document_id)
        .order_by(ExtractionResult.created_at.desc())
        .first()
    )

    return DocumentDetailResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        mime_type=doc.mime_type,
        file_size_bytes=doc.file_size_bytes,
        file_hash=doc.file_hash,
        document_type=doc.document_type,
        status=doc.status,
        decision_outcome=doc.decision_outcome,
        processing_attempts=doc.processing_attempts,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        completed_at=doc.completed_at,
        failure_code=doc.failure_code,
        failure_message=doc.failure_message,
        processing_runs=doc.processing_runs,
        latest_extraction=latest_ext.extracted_data if latest_ext else None,
        latest_decision={"outcome": doc.decision_outcome, "status": doc.status},
    )


@router.get("/{document_id}/results", response_model=DocumentResultResponse, summary="Get extraction and rule results")
def get_document_results(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundException(document_id)

    latest_ext = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.document_id == document_id)
        .order_by(ExtractionResult.created_at.desc())
        .first()
    )

    run = (
        db.query(ProcessingRun)
        .filter(ProcessingRun.document_id == document_id)
        .order_by(ProcessingRun.run_number.desc())
        .first()
    )

    rule_evals = []
    if run and run.rule_evaluations:
        for r in run.rule_evaluations:
            rule_evals.append({
                "rule_code": r.rule_code,
                "rule_version": r.rule_version,
                "status": r.status,
                "severity": r.severity,
                "message": r.message,
                "details": r.details or {},
            })

    return DocumentResultResponse(
        document_id=doc.id,
        status=doc.status,
        decision_outcome=doc.decision_outcome,
        document_type=doc.document_type,
        schema_version=latest_ext.schema_version if latest_ext else "1.0.0",
        extracted_data=latest_ext.extracted_data if latest_ext else None,
        field_evidence=latest_ext.field_evidence if latest_ext else None,
        confidence_data=latest_ext.confidence_data if latest_ext else None,
        validation_results=latest_ext.validation_results if latest_ext else None,
        rule_evaluations=rule_evals,
        created_at=doc.created_at,
    )


@router.get("/{document_id}/file", summary="Download/preview the original uploaded document")
def get_document_file(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundException(document_id)

    storage = get_storage_adapter()
    content = storage.get(doc.storage_key)

    return StreamingResponse(
        io.BytesIO(content),
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.original_filename}"'},
    )


@router.post("/{document_id}/retry", response_model=RetryResponse, summary="Retry an eligible failed document")
def retry_document(
    document_id: str,
    current_user: CurrentUser = Depends(require_role("admin", "operator")),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundException(document_id)

    if doc.status not in ["failed", "review_required"]:
        raise AppException(
            409,
            "NOT_ELIGIBLE_FOR_RETRY",
            f"Document status '{doc.status}' is not eligible for retry.",
        )

    doc.status = "queued"
    doc.failure_code = None
    doc.failure_message = None
    db.commit()

    dispatch_document_processing(doc.id)

    return RetryResponse(
        document_id=doc.id,
        status="queued",
        message="Document processing retry enqueued.",
    )
