import re
from typing import Dict, Any, List


class ClassificationResult:
    def __init__(
        self,
        predicted_type: str,
        confidence_score: float,
        classifier_id: str = "rule_baseline_v1",
        warnings: List[str] = None,
    ):
        self.predicted_type = predicted_type
        self.confidence_score = confidence_score
        self.classifier_id = classifier_id
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_type": self.predicted_type,
            "confidence_score": self.confidence_score,
            "classifier_id": self.classifier_id,
            "warnings": self.warnings,
        }


class ClassificationService:
    INVOICE_KEYWORDS = [
        r"\binvoice\b",
        r"\btax\s+invoice\b",
        r"\bbill\s+to\b",
        r"\binvoice\s+no\b",
        r"\binvoice\s+number\b",
        r"\bdue\s+date\b",
        r"\bsubtotal\b",
        r"\btotal\s+amount\b",
    ]

    PURCHASE_ORDER_KEYWORDS = [
        r"\bpurchase\s+order\b",
        r"\bpo\s+number\b",
        r"\bpo\s+no\b",
        r"\border\s+date\b",
        r"\bvendor\s+reference\b",
    ]

    RECEIPT_KEYWORDS = [
        r"\breceipt\b",
        r"\bcash\s+receipt\b",
        r"\bpayment\s+receipt\b",
        r"\bamount\s+paid\b",
        r"\bchange\s+due\b",
    ]

    CONTRACT_KEYWORDS = [
        r"\bagreement\b",
        r"\bcontract\b",
        r"\bterms\s+and\s+conditions\b",
        r"\bparties\s+hereto\b",
        r"\bindemnif\w+\b",
    ]

    @classmethod
    def classify(cls, text: str) -> ClassificationResult:
        if not text or len(text.strip()) < 10:
            return ClassificationResult(
                predicted_type="unknown",
                confidence_score=0.1,
                warnings=["Insufficient extracted text to classify document reliably."],
            )

        lower_text = text.lower()

        scores = {
            "invoice": sum(1 for kw in cls.INVOICE_KEYWORDS if re.search(kw, lower_text)),
            "purchase_order": sum(1 for kw in cls.PURCHASE_ORDER_KEYWORDS if re.search(kw, lower_text)),
            "receipt": sum(1 for kw in cls.RECEIPT_KEYWORDS if re.search(kw, lower_text)),
            "contract": sum(1 for kw in cls.CONTRACT_KEYWORDS if re.search(kw, lower_text)),
        }

        # Normalize max potential matches
        weighted_scores = {
            "invoice": scores["invoice"] / len(cls.INVOICE_KEYWORDS),
            "purchase_order": scores["purchase_order"] / len(cls.PURCHASE_ORDER_KEYWORDS),
            "receipt": scores["receipt"] / len(cls.RECEIPT_KEYWORDS),
            "contract": scores["contract"] / len(cls.CONTRACT_KEYWORDS),
        }

        best_type, best_ratio = max(weighted_scores.items(), key=lambda x: x[1])

        # If highest score is 0 or very weak, classify as unknown
        if best_ratio < 0.2:
            return ClassificationResult(
                predicted_type="unknown",
                confidence_score=0.2,
                warnings=["Document keywords did not match any known document category."],
            )

        # Check for ambiguity (e.g. both invoice and purchase order have high scores)
        sorted_types = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
        warnings = []
        if len(sorted_types) > 1 and (sorted_types[0][1] - sorted_types[1][1] < 0.15) and sorted_types[1][1] > 0.2:
            warnings.append(
                f"Document is ambiguous between '{sorted_types[0][0]}' and '{sorted_types[1][0]}'."
            )

        # Scale confidence score
        confidence = min(0.98, max(0.4, round(0.5 + (best_ratio * 0.5), 2)))

        return ClassificationResult(
            predicted_type=best_type,
            confidence_score=confidence,
            classifier_id="rule_baseline_v1",
            warnings=warnings,
        )
