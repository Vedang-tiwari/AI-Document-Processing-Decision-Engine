from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.models import Document, ExtractionResult
from backend.app.core.security import get_current_user, CurrentUser, require_role
from backend.app.schemas.review import (
    ReviewQueueResponse,
    ReviewQueueItem,
    ReviewDetailResponse,
    ReviewCorrectionRequest,
    ReviewDecisionRequest,
)
from backend.app.services.review import ReviewService

router = APIRouter(prefix="/reviews", tags=["Human Review"])


@router.get("", response_model=ReviewQueueResponse, summary="List documents awaiting human review")
def list_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_role("reviewer", "admin")),
    db: Session = Depends(get_db),
):
    query = db.query(Document).filter(Document.status == "review_required")
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
        issue_count = 0
        supplier_name = None
        total_amount = None

        if latest_ext:
            conf_data = latest_ext.confidence_data or {}
            conf_score = conf_data.get("document_score")
            val_results = latest_ext.validation_results or {}
            issues = val_results.get("issues", [])
            issue_count = len(issues)
            ext_data = latest_ext.extracted_data or {}
            supplier_name = (ext_data.get("supplier") or {}).get("name")
            total_amount = str(ext_data.get("total_amount", "")) or None

        items.append(
            ReviewQueueItem(
                document_id=d.id,
                original_filename=d.original_filename,
                mime_type=d.mime_type,
                document_type=d.document_type,
                status=d.status,
                created_at=d.created_at,
                confidence_score=conf_score,
                validation_issue_count=issue_count,
                supplier_name=supplier_name,
                total_amount=total_amount,
            )
        )

    return ReviewQueueResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=ReviewDetailResponse, summary="Get full review workspace data")
def get_review_workspace(
    document_id: str,
    current_user: CurrentUser = Depends(require_role("reviewer", "admin")),
    db: Session = Depends(get_db),
):
    detail = ReviewService.get_review_detail(db, document_id)
    return ReviewDetailResponse(**detail)


@router.post("/{document_id}/correct", summary="Submit reviewer corrections for an extraction")
def submit_corrections(
    document_id: str,
    body: ReviewCorrectionRequest,
    current_user: CurrentUser = Depends(require_role("reviewer", "admin")),
    db: Session = Depends(get_db),
):
    return ReviewService.apply_corrections(
        db=db,
        document_id=document_id,
        corrections=body.corrections,
        comment=body.comment,
        reviewer_id=current_user.id,
    )


@router.post("/{document_id}/decision", summary="Submit authorized reviewer decision")
def submit_decision(
    document_id: str,
    body: ReviewDecisionRequest,
    current_user: CurrentUser = Depends(require_role("reviewer", "admin")),
    db: Session = Depends(get_db),
):
    doc = ReviewService.record_decision(
        db=db,
        document_id=document_id,
        decision=body.decision,
        comment=body.comment,
        reviewer_id=current_user.id,
    )
    return {
        "document_id": doc.id,
        "status": doc.status,
        "decision": doc.decision_outcome,
        "message": f"Document successfully marked as '{doc.status}'.",
    }
