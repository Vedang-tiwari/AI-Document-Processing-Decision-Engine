from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field, field_validator


class SupplierInfo(BaseModel):
    name: str = Field(..., min_length=1, description="Supplier or vendor commercial name")
    tax_id: Optional[str] = Field(None, description="Tax identifier e.g. GSTIN, VAT, EIN")


class LineItem(BaseModel):
    description: str
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    amount: Decimal


class InvoiceExtraction(BaseModel):
    document_type: str = "invoice"
    supplier: SupplierInfo
    invoice_number: str = Field(..., min_length=1)
    invoice_date: str = Field(..., description="ISO 8601 date string YYYY-MM-DD")
    due_date: Optional[str] = None
    currency: str = Field("INR", min_length=3, max_length=3)
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)
    purchase_order_reference: Optional[str] = None
    line_items: List[LineItem] = Field(default_factory=list)

    @field_validator("invoice_date", "due_date")
    @classmethod
    def validate_iso_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        try:
            date.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Date '{v}' must be in YYYY-MM-DD ISO format")


class FieldEvidence(BaseModel):
    value: Any
    page: int = 1
    evidence_text: str = ""
    source: str = "native"  # native or ocr
    confidence: float = 1.0


class ValidationIssue(BaseModel):
    code: str
    severity: str  # critical, high, medium, low
    field_path: str
    message: str


class ValidationResult(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
