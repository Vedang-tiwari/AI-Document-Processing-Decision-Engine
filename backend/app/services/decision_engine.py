from typing import Dict, Any, List, Optional
from backend.app.core.config import settings
from backend.app.services.business_rules import RuleResult
from backend.app.services.confidence import ConfidenceAssessmentResult
from backend.app.services.duplicate_detection import DuplicateCheckResult
from backend.app.services.anomaly_detection import AnomalyFlag
from backend.app.schemas.invoice import ValidationResult


class DecisionResult:
    def __init__(
        self,
        outcome: str,  # "auto_eligible", "review_required", "rejected", "blocked_duplicate"
        target_status: str,  # "review_required", "blocked_duplicate", "approved", "rejected"
        reasons: List[str],
        rule_evaluations: List[RuleResult],
    ):
        self.outcome = outcome
        self.target_status = target_status
        self.reasons = reasons
        self.rule_evaluations = rule_evaluations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "target_status": self.target_status,
            "reasons": self.reasons,
            "rule_evaluations": [r.to_dict() for r in self.rule_evaluations],
        }


class DecisionEngineService:
    @classmethod
    def evaluate(
        cls,
        document_type: str,
        validation_result: ValidationResult,
        confidence_result: ConfidenceAssessmentResult,
        duplicate_result: DuplicateCheckResult,
        anomalies: List[AnomalyFlag],
        rule_results: List[RuleResult],
    ) -> DecisionResult:
        reasons: List[str] = []

        # 1. Duplicate check (Hard block)
        if duplicate_result.is_duplicate:
            reasons.append(
                duplicate_result.details.get("reason", "Submission blocked by duplicate policy.")
            )
            return DecisionResult(
                outcome="blocked_duplicate",
                target_status="blocked_duplicate",
                reasons=reasons,
                rule_evaluations=rule_results,
            )

        # 2. Document type support check
        if document_type != "invoice":
            reasons.append(f"Document type '{document_type}' is routed to manual review.")
            return DecisionResult(
                outcome="review_required",
                target_status="review_required",
                reasons=reasons,
                rule_evaluations=rule_results,
            )

        # 3. Schema & Semantic validation
        if not validation_result.is_valid:
            for issue in validation_result.issues:
                if issue.severity in ["critical", "high"]:
                    reasons.append(f"Validation failure ({issue.code}): {issue.message}")

        # 4. Critical anomalies check
        critical_anomalies = [a for a in anomalies if a.severity in ["critical", "high"]]
        for a in critical_anomalies:
            reasons.append(f"Anomaly detected ({a.code}): {a.description}")

        # 5. Business rules results
        failed_rules = [r for r in rule_results if r.status == "failed"]
        for r in failed_rules:
            reasons.append(f"Rule failure ({r.rule_code}): {r.message}")

        # 6. Confidence threshold check
        auto_threshold = settings.CONFIDENCE_AUTO_THRESHOLD
        if confidence_result.document_score < auto_threshold:
            reasons.append(
                f"Document confidence ({confidence_result.document_score}) is below automatic threshold ({auto_threshold})."
            )

        # If any reason exists, route to review
        if reasons:
            return DecisionResult(
                outcome="review_required",
                target_status="review_required",
                reasons=reasons,
                rule_evaluations=rule_results,
            )

        # If all checks pass cleanly
        return DecisionResult(
            outcome="auto_eligible",
            target_status="review_required",  # In MVP decision support, eligible docs can be approved directly or listed for operator signoff
            reasons=["All validation, confidence, duplicate, and business rules passed successfully."],
            rule_evaluations=rule_results,
        )
