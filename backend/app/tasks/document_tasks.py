import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.session import SessionLocal
from backend.app.db.models.models import (
    Document,
    ProcessingRun,
    ExtractionResult,
    RuleEvaluation,
)
from backend.app.storage.local import get_storage_adapter
from backend.app.services.document_parser import DocumentParserService
from backend.app.services.classification import ClassificationService
from backend.app.services.extraction import get_extraction_provider
from backend.app.services.validation import ValidationService
from backend.app.services.confidence import ConfidenceService
from backend.app.services.duplicate_detection import DuplicateDetectionService
from backend.app.services.anomaly_detection import AnomalyDetectionService
from backend.app.services.business_rules import BusinessRuleEngine
from backend.app.services.decision_engine import DecisionEngineService
from backend.app.services.audit import AuditService
from backend.app.services.webhooks import WebhookService
from backend.app.tasks.celery_app import celery_app


def execute_pipeline(document_id: str) -> None:
    db: Session = SessionLocal()
    start_time = time.time()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Cannot process document '{document_id}': record not found.")
            return

        # Advance state
        doc.status = "processing"
        doc.processing_attempts += 1
        db.commit()

        # Create processing run record
        run_number = (
            db.query(ProcessingRun).filter(ProcessingRun.document_id == document_id).count() + 1
        )
        run = ProcessingRun(
            document_id=document_id,
            run_number=run_number,
            pipeline_version="1.0.0",
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Retrieve file content from storage
        storage = get_storage_adapter()
        content = storage.get(doc.storage_key)

        # Phase 2: Parsing & OCR
        parsed_doc = DocumentParserService.parse(content, doc.mime_type)

        # Classification
        classification = ClassificationService.classify(parsed_doc.full_text)
        if doc.document_type in ["unknown", "", None]:
            doc.document_type = classification.predicted_type
            db.commit()

        AuditService.log_event(
            db,
            "document.classification_completed",
            document_id,
            "system",
            None,
            classification.to_dict(),
        )

        # Phase 3: Extraction & Validation
        provider = get_extraction_provider()
        extracted_data, field_evidence = provider.extract_invoice(parsed_doc)

        val_result = ValidationService.validate_invoice(extracted_data)
        conf_result = ConfidenceService.calculate_confidence(
            extracted_data,
            field_evidence,
            val_result,
            parsed_doc.metadata.get("extraction_methods", []),
        )

        # Persist immutable extraction result
        ext_record = ExtractionResult(
            document_id=document_id,
            processing_run_id=run.id,
            schema_version="1.0.0",
            extracted_data=extracted_data,
            field_evidence=field_evidence,
            confidence_data=conf_result.to_dict(),
            validation_results={
                "is_valid": val_result.is_valid,
                "issues": [
                    {
                        "code": i.code,
                        "severity": i.severity,
                        "field_path": i.field_path,
                        "message": i.message,
                    }
                    for i in val_result.issues
                ],
            },
            created_at=datetime.now(timezone.utc),
        )
        db.add(ext_record)
        db.commit()

        AuditService.log_event(
            db,
            "document.extraction_completed",
            document_id,
            "system",
            None,
            {"confidence": conf_result.document_score, "is_valid": val_result.is_valid},
        )

        # Phase 4: Duplicate & Anomaly Detection, Business Rules
        dup_result = DuplicateDetectionService.check_duplicate(
            db, document_id, doc.file_hash, extracted_data
        )
        anomalies = AnomalyDetectionService.detect_anomalies(db, extracted_data)
        rule_evals = BusinessRuleEngine.evaluate_all(
            db,
            extracted_data,
            is_duplicate=dup_result.is_duplicate,
            duplicate_details=dup_result.details,
        )

        # Persist rule evaluations
        for r in rule_evals:
            re_model = RuleEvaluation(
                document_id=document_id,
                processing_run_id=run.id,
                rule_code=r.rule_code,
                rule_version=r.rule_version,
                status=r.status,
                severity=r.severity,
                message=r.message,
                details=r.details,
                created_at=datetime.now(timezone.utc),
            )
            db.add(re_model)
        db.commit()

        # Phase 5: Decision Routing
        decision = DecisionEngineService.evaluate(
            document_type=doc.document_type,
            validation_result=val_result,
            confidence_result=conf_result,
            duplicate_result=dup_result,
            anomalies=anomalies,
            rule_results=rule_evals,
        )

        # Update document decision and status
        doc.decision_outcome = decision.outcome
        doc.status = decision.target_status
        if decision.target_status in ["approved", "rejected", "blocked_duplicate"]:
            doc.completed_at = datetime.now(timezone.utc)

        # Finalize run
        elapsed_ms = int((time.time() - start_time) * 1000)
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.duration_ms = elapsed_ms
        db.commit()

        AuditService.log_event(
            db,
            "document.decision_generated",
            document_id,
            "system",
            None,
            {"outcome": decision.outcome, "status": doc.status, "duration_ms": elapsed_ms},
        )

        # Phase 7: Webhook Dispatch
        WebhookService.dispatch_event(
            db,
            event_type="document.review_required" if doc.status == "review_required" else "document.processing_completed",
            document_id=document_id,
            payload_data={
                "document_id": document_id,
                "status": doc.status,
                "decision_outcome": doc.decision_outcome,
                "total_amount": extracted_data.get("total_amount"),
                "supplier_name": (extracted_data.get("supplier") or {}).get("name"),
            },
        )
        logger.info(f"Pipeline finished for document '{document_id}' with status '{doc.status}'.")

    except Exception as e:
        logger.exception(f"Unexpected error processing document '{document_id}': {e}")
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            if doc.processing_attempts < settings.MAX_PROCESSING_ATTEMPTS:
                doc.status = "queued"
                logger.warning(f"Scheduling retry for document '{document_id}' (attempt {doc.processing_attempts}/{settings.MAX_PROCESSING_ATTEMPTS})")
            else:
                doc.status = "failed"
                doc.failure_code = "PROCESSING_FAILED"
                doc.failure_message = str(e)[:255]
                doc.completed_at = datetime.now(timezone.utc)

                WebhookService.dispatch_event(
                    db,
                    event_type="document.processing_failed",
                    document_id=document_id,
                    payload_data={"error": str(e)[:255]},
                )

            db.commit()
    finally:
        db.close()


@celery_app.task(name="backend.app.tasks.document_tasks.process_document_task")
def process_document_task(document_id: str):
    execute_pipeline(document_id)


def dispatch_document_processing(document_id: str) -> None:
    """
    Unified task dispatcher: runs via Celery (eagerly or worker) or direct synchronous execution.
    """
    try:
        process_document_task.delay(document_id)
    except Exception as e:
        logger.warning(f"Celery dispatch failed: {e}. Executing synchronously.")
        execute_pipeline(document_id)
