import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db.models.models import Document, WebhookEndpoint

client = TestClient(app)


def test_health_endpoints():
    live_resp = client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "ok"

    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"


def test_scenario_a_valid_invoice_upload_and_pipeline():
    # Build simple valid PDF
    pdf_bytes = b"%PDF-1.4\nInvoice Number: INV-E2E-001\nVendor: Acme Global Supplies\nDate: 2026-10-20\nSubtotal: 1000.00\nTax: 180.00\nTotal Amount: 1180.00\n%%EOF"

    response = client.post(
        "/api/v1/documents",
        files={"file": ("invoice_test.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 202
    data = response.json()
    doc_id = data["document_id"]
    assert data["status"] == "queued"

    # Get document detail
    doc_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert doc_resp.status_code == 200
    doc_data = doc_resp.json()
    assert doc_data["id"] == doc_id
    assert doc_data["mime_type"] == "application/pdf"


def test_scenario_c_duplicate_invoice():
    # Same bytes uploaded twice
    pdf_bytes = b"%PDF-1.4\nExact Duplicate Test Payload\n%%EOF"

    # First upload
    res1 = client.post(
        "/api/v1/documents",
        files={"file": ("dup_first.pdf", pdf_bytes, "application/pdf")},
    )
    assert res1.status_code == 202
    doc1_id = res1.json()["document_id"]

    # Second upload with identical bytes
    res2 = client.post(
        "/api/v1/documents",
        files={"file": ("dup_second.pdf", pdf_bytes, "application/pdf")},
    )
    assert res2.status_code == 202
    doc2_id = res2.json()["document_id"]

    # Check that second document is blocked as duplicate
    doc2_resp = client.get(f"/api/v1/documents/{doc2_id}")
    assert doc2_resp.status_code == 200
    assert doc2_resp.json()["status"] == "blocked_duplicate"


def test_scenario_e_human_review_corrections_and_decision():
    import uuid
    import fitz

    # Generate a unique PDF with arithmetic mismatch so it routes to review_required
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(50, 100), f"Invoice Number: INV-REV-{uuid.uuid4().hex[:6]}")
    page.insert_text(fitz.Point(50, 130), "Vendor: Acme Global Supplies")
    page.insert_text(fitz.Point(50, 160), "Date: 2026-10-20")
    page.insert_text(fitz.Point(50, 190), "Subtotal: 10000.00")
    page.insert_text(fitz.Point(50, 220), "Tax: 1800.00")
    page.insert_text(fitz.Point(50, 250), "Total Amount: 15000.00")  # Mismatch (10000 + 1800 != 15000)
    pdf_bytes = doc.tobytes()
    doc.close()

    upload_res = client.post(
        "/api/v1/documents",
        files={"file": ("review_test.pdf", pdf_bytes, "application/pdf")},
    )
    doc_id = upload_res.json()["document_id"]

    # Check review workspace detail
    rev_resp = client.get(f"/api/v1/reviews/{doc_id}")
    assert rev_resp.status_code == 200

    # Submit correction
    corr_resp = client.post(
        f"/api/v1/reviews/{doc_id}/correct",
        json={
            "corrections": {"total_amount": "11800.00"},
            "comment": "Corrected total amount calculation",
        },
    )
    assert corr_resp.status_code == 200
    assert corr_resp.json()["status"] == "success"

    # Submit decision approval
    dec_resp = client.post(
        f"/api/v1/reviews/{doc_id}/decision",
        json={"decision": "approved", "comment": "Approved after manual reconciliation"},
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["status"] == "approved"


def test_webhook_registration_and_signing():
    res = client.post(
        "/api/v1/webhooks",
        json={
            "name": "Integration Test Webhook",
            "url": "https://example.com/webhook",
            "subscribed_events": ["document.processing_completed"],
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "secret" in data
    webhook_id = data["id"]

    # List webhooks should not return the secret
    list_res = client.get("/api/v1/webhooks")
    assert list_res.status_code == 200
    found = [w for w in list_res.json() if w["id"] == webhook_id][0]
    assert "secret" not in found or found.get("secret") is None


def test_dashboard_apis():
    summary_res = client.get("/api/v1/dashboard/summary")
    assert summary_res.status_code == 200
    s_data = summary_res.json()
    assert "total_documents" in s_data
    assert s_data["total_documents"] >= 1

    metrics_res = client.get("/api/v1/dashboard/processing-metrics")
    assert metrics_res.status_code == 200
    m_data = metrics_res.json()
    assert "median_duration_ms" in m_data
    assert "success_rate" in m_data
