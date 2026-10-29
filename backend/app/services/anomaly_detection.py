from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.models import PurchaseOrder, Vendor


class AnomalyFlag:
    def __init__(self, code: str, severity: str, description: str, details: Dict[str, Any] = None):
        self.code = code
        self.severity = severity
        self.description = description
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "description": self.description,
            "details": self.details,
        }


class AnomalyDetectionService:
    @classmethod
    def detect_anomalies(
        cls,
        db: Session,
        extracted_data: Dict[str, Any],
    ) -> List[AnomalyFlag]:
        flags: List[AnomalyFlag] = []

        # 1. Unusually high amount check (> 1,000,000)
        total_str = extracted_data.get("total_amount")
        if total_str:
            try:
                total_val = Decimal(str(total_str))
                if total_val > Decimal("1000000.00"):
                    flags.append(
                        AnomalyFlag(
                            code="UNUSUALLY_HIGH_AMOUNT",
                            severity="high",
                            description=f"Invoice total of {total_val} is unusually large.",
                            details={"total_amount": str(total_val)},
                        )
                    )
            except Exception:
                pass

        # 2. Large difference between invoice and PO if PO reference is present
        po_ref = extracted_data.get("purchase_order_reference")
        if po_ref and total_str:
            try:
                inv_total = Decimal(str(total_str))
                po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_ref).first()
                if po:
                    po_total = Decimal(str(po.total_amount))
                    diff_pct = abs(inv_total - po_total) / max(Decimal("1"), po_total)
                    if diff_pct > Decimal("0.20"):
                        flags.append(
                            AnomalyFlag(
                                code="PO_AMOUNT_LARGE_DISCREPANCY",
                                severity="high",
                                description=(
                                    f"Invoice amount ({inv_total}) deviates by {diff_pct*100:.1f}% "
                                    f"from PO amount ({po_total})."
                                ),
                                details={
                                    "invoice_amount": str(inv_total),
                                    "po_amount": str(po_total),
                                    "po_number": po_ref,
                                },
                            )
                        )
            except Exception:
                pass

        return flags
