from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import yaml
from pathlib import Path

from backend.app.db.models.models import Vendor, PurchaseOrder, BusinessRule
from backend.app.core.config import CONFIG_DIR


class RuleResult:
    def __init__(
        self,
        rule_code: str,
        rule_version: int,
        status: str,  # passed, failed, skipped
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.rule_code = rule_code
        self.rule_version = rule_version
        self.status = status
        self.severity = severity
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "rule_version": self.rule_version,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


class BusinessRuleEngine:
    @staticmethod
    def load_rules_from_config() -> List[Dict[str, Any]]:
        rules_file = CONFIG_DIR / "business_rules.yaml"
        if rules_file.exists():
            with open(rules_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("rules", [])
        return []

    @classmethod
    def evaluate_all(
        cls,
        db: Session,
        extracted_data: Dict[str, Any],
        is_duplicate: bool = False,
        duplicate_details: Optional[Dict[str, Any]] = None,
    ) -> List[RuleResult]:
        rules = cls.load_rules_from_config()
        results: List[RuleResult] = []

        for rule in rules:
            if not rule.get("enabled", True):
                continue

            code = rule.get("rule_code")
            version = rule.get("version", 1)
            severity = rule.get("severity", "high")
            config = rule.get("configuration", {})

            if code == "REQUIRED_FIELDS_PRESENT":
                res = cls._eval_required_fields(extracted_data, config, version, severity)
            elif code == "INVOICE_TOTAL_RECONCILIATION":
                res = cls._eval_reconciliation(extracted_data, config, version, severity)
            elif code == "VENDOR_EXISTS":
                res = cls._eval_vendor(db, extracted_data, config, version, severity)
            elif code == "DUPLICATE_INVOICE_CHECK":
                res = cls._eval_duplicate(is_duplicate, duplicate_details, version, severity)
            elif code == "MAX_AUTO_APPROVAL_AMOUNT":
                res = cls._eval_max_amount(extracted_data, config, version, severity)
            elif code == "PURCHASE_ORDER_MATCH":
                res = cls._eval_po_match(db, extracted_data, config, version, severity)
            else:
                res = RuleResult(
                    rule_code=code,
                    rule_version=version,
                    status="skipped",
                    severity=severity,
                    message=f"Rule {code} has no implementation.",
                )

            results.append(res)

        return results

    @staticmethod
    def _eval_required_fields(
        data: Dict[str, Any], config: Dict[str, Any], version: int, severity: str
    ) -> RuleResult:
        fields = config.get("required_fields", ["supplier.name", "invoice_number", "invoice_date", "currency", "total_amount"])
        missing = []
        for f in fields:
            if "." in f:
                p1, p2 = f.split(".")
                v = data.get(p1, {}).get(p2) if isinstance(data.get(p1), dict) else None
            else:
                v = data.get(f)
            if v is None or str(v).strip() == "":
                missing.append(f)

        if missing:
            return RuleResult(
                rule_code="REQUIRED_FIELDS_PRESENT",
                rule_version=version,
                status="failed",
                severity=severity,
                message=f"Missing required fields: {', '.join(missing)}.",
                details={"missing_fields": missing},
            )
        return RuleResult(
            rule_code="REQUIRED_FIELDS_PRESENT",
            rule_version=version,
            status="passed",
            severity=severity,
            message="All required invoice fields are present.",
        )

    @staticmethod
    def _eval_reconciliation(
        data: Dict[str, Any], config: Dict[str, Any], version: int, severity: str
    ) -> RuleResult:
        tol = Decimal(str(config.get("amount_tolerance", "1.00")))
        try:
            subtotal = Decimal(str(data.get("subtotal", 0)))
            tax = Decimal(str(data.get("tax_amount", 0)))
            total = Decimal(str(data.get("total_amount", 0)))
            diff = abs((subtotal + tax) - total)
            if diff <= tol:
                return RuleResult(
                    rule_code="INVOICE_TOTAL_RECONCILIATION",
                    rule_version=version,
                    status="passed",
                    severity=severity,
                    message="Invoice total reconciles with subtotal and tax within tolerance.",
                    details={"difference": str(diff), "tolerance": str(tol)},
                )
            else:
                return RuleResult(
                    rule_code="INVOICE_TOTAL_RECONCILIATION",
                    rule_version=version,
                    status="failed",
                    severity=severity,
                    message=f"Total {total} does not equal subtotal {subtotal} + tax {tax} (diff {diff} > {tol}).",
                    details={"subtotal": str(subtotal), "tax": str(tax), "total": str(total), "diff": str(diff)},
                )
        except (InvalidOperation, TypeError):
            return RuleResult(
                rule_code="INVOICE_TOTAL_RECONCILIATION",
                rule_version=version,
                status="failed",
                severity=severity,
                message="Cannot perform arithmetic reconciliation: invalid decimal amounts.",
            )

    @staticmethod
    def _eval_vendor(
        db: Session, data: Dict[str, Any], config: Dict[str, Any], version: int, severity: str
    ) -> RuleResult:
        supp = data.get("supplier") or {}
        name = supp.get("name", "").strip() if isinstance(supp, dict) else ""
        if not name:
            return RuleResult(
                rule_code="VENDOR_EXISTS",
                rule_version=version,
                status="failed",
                severity=severity,
                message="Supplier name is absent; cannot verify vendor registry.",
            )

        # Check vendor table (case-insensitive name match or tax_id match)
        v = db.query(Vendor).filter(Vendor.normalized_name == name.lower()).first()
        if not v and supp.get("tax_id"):
            v = db.query(Vendor).filter(Vendor.tax_id == supp.get("tax_id")).first()

        if v and v.is_active:
            return RuleResult(
                rule_code="VENDOR_EXISTS",
                rule_version=version,
                status="passed",
                severity=severity,
                message=f"Vendor '{name}' is verified in vendor registry (ID: {v.id}).",
                details={"vendor_id": v.id, "vendor_name": v.name},
            )
        elif v and not v.is_active:
            return RuleResult(
                rule_code="VENDOR_EXISTS",
                rule_version=version,
                status="failed",
                severity=severity,
                message=f"Vendor '{name}' is deactivated in registry.",
                details={"vendor_id": v.id},
            )
        else:
            return RuleResult(
                rule_code="VENDOR_EXISTS",
                rule_version=version,
                status="failed",
                severity=severity,
                message=f"Supplier '{name}' was not found in registered vendor database.",
            )

    @staticmethod
    def _eval_duplicate(
        is_duplicate: bool, details: Optional[Dict[str, Any]], version: int, severity: str
    ) -> RuleResult:
        if is_duplicate:
            return RuleResult(
                rule_code="DUPLICATE_INVOICE_CHECK",
                rule_version=version,
                status="failed",
                severity=severity,
                message="Document violates duplicate policy.",
                details=details or {},
            )
        return RuleResult(
            rule_code="DUPLICATE_INVOICE_CHECK",
            rule_version=version,
            status="passed",
            severity=severity,
            message="Duplicate invoice checks passed.",
        )

    @staticmethod
    def _eval_max_amount(
        data: Dict[str, Any], config: Dict[str, Any], version: int, severity: str
    ) -> RuleResult:
        limit = Decimal(str(config.get("max_amount", "25000.00")))
        try:
            total = Decimal(str(data.get("total_amount", 0)))
            if total <= limit:
                return RuleResult(
                    rule_code="MAX_AUTO_APPROVAL_AMOUNT",
                    rule_version=version,
                    status="passed",
                    severity=severity,
                    message=f"Invoice total {total} is within auto-processing limit of {limit}.",
                    details={"total_amount": str(total), "limit": str(limit)},
                )
            else:
                return RuleResult(
                    rule_code="MAX_AUTO_APPROVAL_AMOUNT",
                    rule_version=version,
                    status="failed",
                    severity=severity,
                    message=f"Invoice total {total} exceeds automatic threshold of {limit}. Human review required.",
                    details={"total_amount": str(total), "limit": str(limit)},
                )
        except Exception:
            return RuleResult(
                rule_code="MAX_AUTO_APPROVAL_AMOUNT",
                rule_version=version,
                status="failed",
                severity=severity,
                message="Invalid total amount for threshold check.",
            )

    @staticmethod
    def _eval_po_match(
        db: Session, data: Dict[str, Any], config: Dict[str, Any], version: int, severity: str
    ) -> RuleResult:
        po_ref = data.get("purchase_order_reference")
        if not po_ref:
            # If PO is not required when absent, pass or skip
            return RuleResult(
                rule_code="PURCHASE_ORDER_MATCH",
                rule_version=version,
                status="skipped",
                severity="low",
                message="No Purchase Order reference specified on invoice.",
            )

        po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_ref).first()
        if not po:
            return RuleResult(
                rule_code="PURCHASE_ORDER_MATCH",
                rule_version=version,
                status="failed",
                severity=severity,
                message=f"Referenced Purchase Order '{po_ref}' does not exist in PO registry.",
            )

        tol = Decimal(str(config.get("amount_tolerance", "5.00")))
        try:
            inv_total = Decimal(str(data.get("total_amount", 0)))
            po_total = Decimal(str(po.total_amount))
            diff = abs(inv_total - po_total)
            if diff <= tol:
                return RuleResult(
                    rule_code="PURCHASE_ORDER_MATCH",
                    rule_version=version,
                    status="passed",
                    severity=severity,
                    message=f"Invoice total matches PO '{po_ref}' within {tol} tolerance.",
                    details={"po_total": str(po_total), "inv_total": str(inv_total), "diff": str(diff)},
                )
            else:
                return RuleResult(
                    rule_code="PURCHASE_ORDER_MATCH",
                    rule_version=version,
                    status="failed",
                    severity=severity,
                    message=f"Invoice amount ({inv_total}) differs from PO amount ({po_total}) by {diff}.",
                    details={"po_total": str(po_total), "inv_total": str(inv_total), "diff": str(diff)},
                )
        except Exception as e:
            return RuleResult(
                rule_code="PURCHASE_ORDER_MATCH",
                rule_version=version,
                status="failed",
                severity=severity,
                message=f"PO match evaluation error: {e}",
            )
