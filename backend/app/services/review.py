from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.db.models.models import Document, ExtractionResult, ReviewRecord, ProcessingRun
from backend.app.core.exceptions import (
    DocumentNotFoundException,
    InvalidStateTransitionException,
    AppException,
)
from backend.app.services.audit import AuditService
from backend.app.services.validation import ValidationService
from backend.app.services.business_rules import BusinessRuleEngine
from backend.app.core.logging import logger


class ReviewService:
    @staticmethod
    def get_review_detail(db: Session, document_id: str) -> Dict[str, Any]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise DocumentNotFoundException(document_id)

        latest_ext = (
            db.query(ExtractionResult)
            .filter(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .first()
        )

        revisions = (
            db.query(ReviewRecord)
            .filter(ReviewRecord.document_id == document_id)
            .order_by(ReviewRecord.created_at.asc())
            .all()
        )

        evaluations = (
            db.query(ProcessingRun)
            .filter(ProcessingRun.document_id == document_id)
            .order_by(ProcessingRun.run_number.desc())
            .first()
        )

        rules_list = []
        if evaluations and evaluations.rule_evaluations:
            for r in evaluations.rule_evaluations:
                rules_list.append({
                    "rule_code": r.rule_code,
                    "rule_version": r.rule_version,
                    "status": r.status,
                    "severity": r.severity,
                    "message": r.message,
                    "details": r.details,
                })

        return {
            "document_id": doc.id,
            "original_filename": doc.original_filename,
            "mime_type": doc.mime_type,
            "document_type": doc.document_type,
            "status": doc.status,
            "decision_outcome": doc.decision_outcome,
            "extracted_data": latest_ext.extracted_data if latest_ext else None,
            "field_evidence": latest_ext.field_evidence if latest_ext else None,
            "confidence_data": latest_ext.confidence_data if latest_ext else None,
            "validation_results": latest_ext.validation_results if latest_ext else None,
            "rule_evaluations": rules_list,
            "revisions": [
                {
                    "id": rev.id,
                    "reviewer_id": rev.reviewer_id,
                    "action": rev.action,
                    "corrected_data": rev.corrected_data,
                    "comment": rev.comment,
                    "created_at": rev.created_at,
                }
                for rev in revisions
            ],
            "created_at": doc.created_at,
        }

    @staticmethod
    def apply_corrections(
        db: Session,
        document_id: str,
        corrections: Dict[str, Any],
        comment: Optional[str],
        reviewer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise DocumentNotFoundException(document_id)

        if doc.status not in ["review_required", "queued"]:
            raise InvalidStateTransitionException(doc.status, "review_required")

        latest_ext = (
            db.query(ExtractionResult)
            .filter(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .first()
        )
        if not latest_ext:
            raise AppException(400, "NO_EXTRACTION_FOUND", "Document has no extraction record to correct.")

        # Create copy of extracted data and merge corrections
        current_data = dict(latest_ext.extracted_data)
        for k, v in corrections.items():
            if "." in k:
                p1, p2 = k.split(".", 1)
                if p1 not in current_data or not isinstance(current_data[p1], dict):
                    current_data[p1] = {}
                current_data[p1][p2] = v
            else:
                current_data[k] = v

        # Rerun validation on corrected data
        new_val = ValidationService.validate_invoice(current_data)
        val_dict = {
            "is_valid": new_val.is_valid,
            "issues": [
                {
                    "code": i.code,
                    "severity": i.severity,
                    "field_path": i.field_path,
                    "message": i.message,
                }
                for i in new_val.issues
            ],
        }

        # Verify reviewer_id exists in users table to satisfy foreign key
        from backend.app.db.models.models import User
        valid_reviewer_id = None
        if reviewer_id:
            if db.query(User).filter(User.id == reviewer_id).first():
                valid_reviewer_id = reviewer_id

        # Persist review record (preserving history)
        review_record = ReviewRecord(
            document_id=doc.id,
            reviewer_id=valid_reviewer_id,
            action="corrected",
            original_extraction_id=latest_ext.id,
            corrected_data=corrections,
            comment=comment,
            created_at=datetime.now(timezone.utc),
        )
        db.add(review_record)

        # Update latest extraction with corrected data and new validation
        latest_ext.extracted_data = current_data
        latest_ext.validation_results = val_dict

        # Audit event
        AuditService.log_event(
            db=db,
            event_type="document.corrected",
            document_id=doc.id,
            actor_type="reviewer" if reviewer_id else "system",
            actor_id=reviewer_id,
            metadata={"fields_corrected": list(corrections.keys()), "comment": comment},
        )

        db.commit()
        return {"status": "success", "message": "Corrections saved and revalidated."}

    @staticmethod
    def record_decision(
        db: Session,
        document_id: str,
        decision: str,  # "approved" or "rejected"
        comment: Optional[str],
        reviewer_id: Optional[str] = None,
    ) -> Document:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise DocumentNotFoundException(document_id)

        if decision not in ["approved", "rejected"]:
            raise AppException(400, "INVALID_DECISION", "Decision must be either 'approved' or 'rejected'.")

        # Check allowed transitions
        if doc.status not in ["review_required", "queued", "processing"]:
            raise InvalidStateTransitionException(doc.status, decision)

        # Check mandatory constraints: cannot approve a document with critical arithmetic errors unless exception
        latest_ext = (
            db.query(ExtractionResult)
            .filter(ExtractionResult.document_id == document_id)
            .order_by(ExtractionResult.created_at.desc())
            .first()
        )

        if decision == "approved" and latest_ext:
            val_results = latest_ext.validation_results or {}
            issues = val_results.get("issues", [])
            critical_issues = [i for i in issues if i.get("severity") == "critical"]
            if critical_issues:
                raise AppException(
                    422,
                    "CANNOT_APPROVE_CRITICAL_ERRORS",
                    f"Cannot approve document with critical validation issues: {critical_issues[0].get('message')}",
                )

        doc.status = decision
        doc.decision_outcome = decision
        doc.completed_at = datetime.now(timezone.utc)

        # Record review record
        valid_reviewer_id = None
        if reviewer_id:
            from backend.app.db.models.models import User
            if db.query(User).filter(User.id == reviewer_id).first():
                valid_reviewer_id = reviewer_id

        rev = ReviewRecord(
            document_id=doc.id,
            reviewer_id=valid_reviewer_id,
            action=decision,
            original_extraction_id=latest_ext.id if latest_ext else None,
            corrected_data={},
            comment=comment,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rev)

        # Audit event
        AuditService.log_event(
            db=db,
            event_type=f"document.{decision}",
            document_id=doc.id,
            actor_type="reviewer" if reviewer_id else "system",
            actor_id=reviewer_id,
            metadata={"decision": decision, "comment": comment},
        )

        db.commit()
        db.refresh(doc)
        logger.info(f"Document '{doc.id}' finalized with decision '{decision}' by reviewer '{reviewer_id}'.")
        return doc
