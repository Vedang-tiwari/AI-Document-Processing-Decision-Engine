from decimal import Decimal
from backend.app.services.business_rules import BusinessRuleEngine
from backend.app.db.session import SessionLocal
from backend.app.db.models.models import Vendor, PurchaseOrder


def test_rule_reconciliation_pass():
    data = {
        "subtotal": "20000.00",
        "tax_amount": "3600.00",
        "total_amount": "23600.00",
    }
    config = {"amount_tolerance": "1.00"}
    res = BusinessRuleEngine._eval_reconciliation(data, config, version=1, severity="high")
    assert res.status == "passed"


def test_rule_reconciliation_fail():
    data = {
        "subtotal": "20000.00",
        "tax_amount": "3600.00",
        "total_amount": "25000.00",
    }
    config = {"amount_tolerance": "1.00"}
    res = BusinessRuleEngine._eval_reconciliation(data, config, version=1, severity="high")
    assert res.status == "failed"


def test_rule_max_amount():
    config = {"max_amount": "25000.00"}
    pass_res = BusinessRuleEngine._eval_max_amount({"total_amount": "23600.00"}, config, 1, "medium")
    assert pass_res.status == "passed"

    fail_res = BusinessRuleEngine._eval_max_amount({"total_amount": "47200.00"}, config, 1, "medium")
    assert fail_res.status == "failed"


def test_rule_vendor_exists():
    db = SessionLocal()
    try:
        # Acme Global Supplies was seeded
        pass_res = BusinessRuleEngine._eval_vendor(
            db, {"supplier": {"name": "Acme Global Supplies"}}, {}, 1, "high"
        )
        assert pass_res.status == "passed"

        fail_res = BusinessRuleEngine._eval_vendor(
            db, {"supplier": {"name": "Nonexistent Fake Vendor"}}, {}, 1, "high"
        )
        assert fail_res.status == "failed"
    finally:
        db.close()
