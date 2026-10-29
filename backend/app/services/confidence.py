from typing import Dict, Any, List
from backend.app.schemas.invoice import ValidationResult


class ConfidenceAssessmentResult:
    def __init__(
        self,
        document_score: float,
        assessment: str,
        signals: Dict[str, Any],
        reasons: List[str],
    ):
        self.document_score = document_score
        self.assessment = assessment
        self.signals = signals
        self.reasons = reasons

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_score": self.document_score,
            "assessment": self.assessment,
            "signals": self.signals,
            "reasons": self.reasons,
        }


class ConfidenceService:
    REQUIRED_KEYS = ["supplier.name", "invoice_number", "invoice_date", "total_amount", "subtotal", "tax_amount"]

    @classmethod
    def calculate_confidence(
        cls,
        extracted_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
        validation_result: ValidationResult,
        ocr_methods: List[str],
    ) -> ConfidenceAssessmentResult:
        reasons: List[str] = []
        base_score = 1.0

        # 1. Required fields presence check
        missing_fields = []
        for key in cls.REQUIRED_KEYS:
            if "." in key:
                parts = key.split(".")
                val = extracted_data.get(parts[0], {}).get(parts[1]) if isinstance(extracted_data.get(parts[0]), dict) else None
            else:
                val = extracted_data.get(key)
            if val is None or str(val).strip() == "":
                missing_fields.append(key)

        required_fields_present = len(missing_fields) == 0
        if not required_fields_present:
            base_score -= 0.35
            reasons.append(f"Missing required extraction fields: {', '.join(missing_fields)}")

        # 2. Schema / Validation Result
        schema_valid = validation_result.is_valid
        if not schema_valid:
            critical_count = sum(1 for i in validation_result.issues if i.severity == "critical")
            high_count = sum(1 for i in validation_result.issues if i.severity == "high")
            penalty = (critical_count * 0.20) + (high_count * 0.10)
            base_score -= min(0.40, penalty)
            for iss in validation_result.issues:
                if iss.severity in ["critical", "high"]:
                    reasons.append(f"Validation issue: {iss.message}")

        # 3. Evidence Coverage
        extracted_count = len(cls.REQUIRED_KEYS)
        covered_count = sum(1 for k in cls.REQUIRED_KEYS if k in evidence_data)
        evidence_coverage = round(covered_count / max(1, extracted_count), 2)
        if evidence_coverage < 0.8:
            base_score -= (0.8 - evidence_coverage) * 0.25
            reasons.append(f"Low evidence coverage ({evidence_coverage * 100:.0f}%)")

        # 4. Cross-field consistency
        has_arithmetic_issue = any(i.code == "INVOICE_TOTAL_MISMATCH" for i in validation_result.issues)
        cross_field_consistency = not has_arithmetic_issue
        if not cross_field_consistency:
            base_score -= 0.15
            reasons.append("Totals do not reconcile arithmetically")

        # 5. OCR Quality penalty if scanned OCR was needed
        if "ocr" in ocr_methods and "native" not in ocr_methods:
            base_score -= 0.05
            reasons.append("Document processed via OCR; slight confidence penalty applied")

        final_score = round(max(0.05, min(1.0, base_score)), 2)

        if final_score >= 0.85:
            assessment = "high"
        elif final_score >= 0.70:
            assessment = "medium"
        else:
            assessment = "low"

        signals = {
            "required_fields_present": required_fields_present,
            "schema_valid": schema_valid,
            "evidence_coverage": evidence_coverage,
            "cross_field_consistency": cross_field_consistency,
            "ocr_methods": ocr_methods,
        }

        return ConfidenceAssessmentResult(
            document_score=final_score,
            assessment=assessment,
            signals=signals,
            reasons=reasons,
        )
