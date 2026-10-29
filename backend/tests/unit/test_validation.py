from decimal import Decimal
from backend.app.services.validation import ValidationService


def test_valid_invoice_validation():
    data = {
        "supplier": {"name": "Acme Global Supplies", "tax_id": "GSTIN-123"},
        "invoice_number": "INV-1001",
        "invoice_date": "2026-10-20",
        "due_date": "2026-11-20",
        "currency": "INR",
        "subtotal": "20000.00",
        "tax_amount": "3600.00",
        "total_amount": "23600.00",
    }
    result = ValidationService.validate_invoice(data)
    assert result.is_valid is True
    assert len(result.issues) == 0


def test_invoice_arithmetic_mismatch():
    data = {
        "supplier": {"name": "Acme Global Supplies"},
        "invoice_number": "INV-1002",
        "invoice_date": "2026-10-20",
        "currency": "INR",
        "subtotal": "20000.00",
        "tax_amount": "3600.00",
        "total_amount": "25000.00",  # Expected 23600.00
    }
    result = ValidationService.validate_invoice(data, amount_tolerance=Decimal("1.00"))
    assert result.is_valid is False
    codes = [i.code for i in result.issues]
    assert "INVOICE_TOTAL_MISMATCH" in codes


def test_missing_required_fields():
    data = {
        "currency": "INR",
        "subtotal": "20000.00",
        "tax_amount": "3600.00",
        "total_amount": "23600.00",
    }
    result = ValidationService.validate_invoice(data)
    assert result.is_valid is False
    codes = [i.code for i in result.issues]
    assert "MISSING_REQUIRED_FIELD" in codes


def test_due_date_before_invoice_date():
    data = {
        "supplier": {"name": "Acme Global Supplies"},
        "invoice_number": "INV-1003",
        "invoice_date": "2026-10-20",
        "due_date": "2026-10-10",  # Earlier than invoice date
        "currency": "INR",
        "subtotal": "1000.00",
        "tax_amount": "100.00",
        "total_amount": "1100.00",
    }
    result = ValidationService.validate_invoice(data)
    assert result.is_valid is False
    codes = [i.code for i in result.issues]
    assert "DUE_DATE_BEFORE_INVOICE_DATE" in codes
