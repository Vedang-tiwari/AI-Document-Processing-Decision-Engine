from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.db.models.models import Document, ExtractionResult


class DuplicateCheckResult:
    def __init__(
        self,
        is_duplicate: bool,
        duplicate_type: Optional[str] = None,  # "exact" or "business"
        original_document_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.is_duplicate = is_duplicate
        self.duplicate_type = duplicate_type
        self.original_document_id = original_document_id
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_duplicate": self.is_duplicate,
            "duplicate_type": self.duplicate_type,
            "original_document_id": self.original_document_id,
            "details": self.details,
        }


class DuplicateDetectionService:
    @classmethod
    def check_duplicate(
        cls,
        db: Session,
        current_doc_id: str,
        file_hash: str,
        extracted_data: Dict[str, Any],
    ) -> DuplicateCheckResult:
        # 1. Exact Duplicate by File Hash
        exact_match = (
            db.query(Document)
            .filter(Document.file_hash == file_hash, Document.id != current_doc_id)
            .first()
        )
        if exact_match:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_type="exact",
                original_document_id=exact_match.id,
                details={
                    "reason": "Exact byte-identical file has previously been processed.",
                    "matched_document_id": exact_match.id,
                    "matched_filename": exact_match.original_filename,
                    "matched_status": exact_match.status,
                },
            )

        # 2. Business Duplicate Check
        # Match supplier name + invoice number
        supplier = extracted_data.get("supplier") or {}
        supplier_name = supplier.get("name", "").strip().lower() if isinstance(supplier, dict) else ""
        invoice_number = str(extracted_data.get("invoice_number", "")).strip().lower()
        total_amount = str(extracted_data.get("total_amount", "")).strip()

        if supplier_name and invoice_number:
            # Query recent extraction results of other documents
            prior_extractions = (
                db.query(ExtractionResult, Document)
                .join(Document, Document.id == ExtractionResult.document_id)
                .filter(Document.id != current_doc_id, Document.status.in_(["approved", "review_required", "queued", "processing"]))
                .all()
            )

            for ext, doc in prior_extractions:
                data = ext.extracted_data or {}
                prior_supp = (data.get("supplier") or {}).get("name", "").strip().lower() if isinstance(data.get("supplier"), dict) else ""
                prior_inv = str(data.get("invoice_number", "")).strip().lower()

                if prior_supp == supplier_name and prior_inv == invoice_number:
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        duplicate_type="business",
                        original_document_id=doc.id,
                        details={
                            "reason": f"Invoice number '{invoice_number}' from supplier '{supplier_name}' already exists in record '{doc.id}'.",
                            "matched_document_id": doc.id,
                            "matched_invoice_number": prior_inv,
                            "matched_total_amount": str(data.get("total_amount", "")),
                        },
                    )

        return DuplicateCheckResult(is_duplicate=False)
