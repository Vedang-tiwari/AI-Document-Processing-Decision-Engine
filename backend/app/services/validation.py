from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from backend.app.schemas.invoice import ValidationIssue, ValidationResult


class ValidationService:
    @classmethod
    def validate_invoice(
        cls,
        extracted_data: Dict[str, Any],
        amount_tolerance: Decimal = Decimal("1.00"),
    ) -> ValidationResult:
        issues: List[ValidationIssue] = []

        # 1. Structural Checks
        # Supplier
        supplier = extracted_data.get("supplier") or {}
        supplier_name = supplier.get("name") if isinstance(supplier, dict) else None
        if not supplier_name or not str(supplier_name).strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_REQUIRED_FIELD",
                    severity="critical",
                    field_path="supplier.name",
                    message="Supplier name is required.",
                )
            )

        # Invoice Number
        invoice_number = extracted_data.get("invoice_number")
        if not invoice_number or not str(invoice_number).strip():
            issues.append(
                ValidationIssue(
                    code="MISSING_REQUIRED_FIELD",
                    severity="critical",
                    field_path="invoice_number",
                    message="Invoice number is required.",
                )
            )

        # Invoice Date
        invoice_date_val = None
        invoice_date_str = extracted_data.get("invoice_date")
        if not invoice_date_str:
            issues.append(
                ValidationIssue(
                    code="MISSING_REQUIRED_FIELD",
                    severity="critical",
                    field_path="invoice_date",
                    message="Invoice date is required.",
                )
            )
        else:
            try:
                invoice_date_val = date.fromisoformat(str(invoice_date_str))
                # Semantic Date plausibility
                today = date.today()
                if invoice_date_val > today + timedelta(days=30):
                    issues.append(
                        ValidationIssue(
                            code="FUTURE_INVOICE_DATE",
                            severity="high",
                            field_path="invoice_date",
                            message=f"Invoice date {invoice_date_str} is in the future.",
                        )
                    )
                if invoice_date_val < today - timedelta(days=365 * 10):
                    issues.append(
                        ValidationIssue(
                            code="STALE_INVOICE_DATE",
                            severity="medium",
                            field_path="invoice_date",
                            message=f"Invoice date {invoice_date_str} is older than 10 years.",
                        )
                    )
            except ValueError:
                issues.append(
                    ValidationIssue(
                        code="INVALID_DATE_FORMAT",
                        severity="critical",
                        field_path="invoice_date",
                        message=f"Invoice date '{invoice_date_str}' is not in valid YYYY-MM-DD format.",
                    )
                )

        # Due Date
        due_date_str = extracted_data.get("due_date")
        if due_date_str:
            try:
                due_date_val = date.fromisoformat(str(due_date_str))
                if invoice_date_val and due_date_val < invoice_date_val:
                    issues.append(
                        ValidationIssue(
                            code="DUE_DATE_BEFORE_INVOICE_DATE",
                            severity="high",
                            field_path="due_date",
                            message=f"Due date {due_date_str} is earlier than invoice date {invoice_date_str}.",
                        )
                    )
            except ValueError:
                issues.append(
                    ValidationIssue(
                        code="INVALID_DATE_FORMAT",
                        severity="medium",
                        field_path="due_date",
                        message=f"Due date '{due_date_str}' is not in valid YYYY-MM-DD format.",
                    )
                )

        # Monetary fields parsing
        def parse_decimal(field_name: str, required: bool = True) -> Optional[Decimal]:
            val = extracted_data.get(field_name)
            if val is None or val == "":
                if required:
                    issues.append(
                        ValidationIssue(
                            code="MISSING_REQUIRED_FIELD",
                            severity="critical",
                            field_path=field_name,
                            message=f"Amount field '{field_name}' is required.",
                        )
                    )
                return None
            try:
                d = Decimal(str(val))
                if d < 0:
                    issues.append(
                        ValidationIssue(
                            code="NEGATIVE_AMOUNT",
                            severity="critical",
                            field_path=field_name,
                            message=f"Amount field '{field_name}' cannot be negative.",
                        )
                    )
                return d
            except (InvalidOperation, TypeError):
                issues.append(
                    ValidationIssue(
                        code="INVALID_DECIMAL",
                        severity="critical",
                        field_path=field_name,
                        message=f"Field '{field_name}' value '{val}' is not a valid decimal number.",
                    )
                )
                return None

        subtotal = parse_decimal("subtotal", required=True)
        tax_amount = parse_decimal("tax_amount", required=True)
        total_amount = parse_decimal("total_amount", required=True)

        # 2. Semantic Arithmetic Reconciliation
        if subtotal is not None and tax_amount is not None and total_amount is not None:
            expected_total = subtotal + tax_amount
            diff = abs(expected_total - total_amount)
            if diff > amount_tolerance:
                issues.append(
                    ValidationIssue(
                        code="INVOICE_TOTAL_MISMATCH",
                        severity="high",
                        field_path="total_amount",
                        message=(
                            f"Total amount ({total_amount}) does not reconcile with "
                            f"subtotal ({subtotal}) + tax ({tax_amount}) = {expected_total} "
                            f"(diff {diff} exceeds tolerance {amount_tolerance})."
                        ),
                    )
                )

        # Line items validation
        line_items = extracted_data.get("line_items", [])
        if isinstance(line_items, list):
            for idx, item in enumerate(line_items):
                if isinstance(item, dict):
                    if not item.get("description"):
                        issues.append(
                            ValidationIssue(
                                code="LINE_ITEM_MISSING_DESCRIPTION",
                                severity="low",
                                field_path=f"line_items[{idx}].description",
                                message=f"Line item at index {idx} has empty description.",
                            )
                        )

        # Document is structurally & semantically valid if there are no critical or high severity issues
        is_valid = not any(i.severity in ["critical", "high"] for i in issues)

        return ValidationResult(is_valid=is_valid, issues=issues)
