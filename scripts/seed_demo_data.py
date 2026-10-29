import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

from backend.app.db.session import SessionLocal, engine
from backend.app.db.base import Base
from backend.app.db.models.models import (
    User,
    Vendor,
    PurchaseOrder,
    BusinessRule,
)
from backend.app.core.security import hash_password
from backend.app.services.business_rules import BusinessRuleEngine
from backend.app.services.ingestion import IngestionService
from backend.app.tasks.document_tasks import execute_pipeline


def create_sample_pdf(filepath: Path, content_lines: list[str]) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Draw header banner
    page.draw_rect(fitz.Rect(40, 40, 555, 90), color=(0.1, 0.2, 0.45), fill=(0.1, 0.2, 0.45))
    page.insert_text(fitz.Point(50, 75), "COMMERCIAL TAX INVOICE", fontsize=18, color=(1, 1, 1))

    # Draw body lines
    y = 120
    for line in content_lines:
        if line.startswith("---"):
            page.draw_line(fitz.Point(40, y - 5), fitz.Point(555, y - 5), color=(0.7, 0.7, 0.7), width=1)
            y += 10
            continue
        is_bold = any(k in line for k in ["Vendor:", "Total Amount:", "INVOICE"])
        page.insert_text(
            fitz.Point(50, y),
            line,
            fontsize=12 if is_bold else 10,
            color=(0.1, 0.1, 0.1),
        )
        y += 20

    doc.save(str(filepath))
    doc.close()


def create_sample_image(filepath: Path, lines: list[str]) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (700, 900), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.rectangle([30, 30, 670, 80], fill=(240, 243, 246), outline=(200, 205, 210))
    draw.text((45, 45), "INVOICE RECEIPT", fill=(30, 40, 60))

    y = 110
    for l in lines:
        draw.text((50, y), l, fill=(40, 40, 40))
        y += 28

    img.save(str(filepath))


def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Users
        users = [
            ("admin@example.com", "Admin@123", "admin"),
            ("reviewer@example.com", "Reviewer@123", "reviewer"),
            ("operator@example.com", "Operator@123", "operator"),
        ]
        for email, pwd, role in users:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                u = User(
                    email=email,
                    password_hash=hash_password(pwd),
                    role=role,
                    is_active=True,
                )
                db.add(u)
        db.commit()
        print("Default users seeded.")

        # 2. Vendors
        vendors_data = [
            ("Acme Global Supplies", "acme global supplies", "GSTIN-27AAACA1234A1Z5"),
            ("TechFlow Solutions", "techflow solutions", "GSTIN-07BBBCB5678B2Z1"),
            ("Apex Logistics", "apex logistics", "GSTIN-19CCCCC9012C3Z8"),
        ]
        for name, norm_name, tax_id in vendors_data:
            existing = db.query(Vendor).filter(Vendor.normalized_name == norm_name).first()
            if not existing:
                v = Vendor(
                    name=name,
                    normalized_name=norm_name,
                    tax_id=tax_id,
                    is_active=True,
                )
                db.add(v)
        db.commit()
        print("Vendor registry seeded.")

        # 3. Purchase Orders
        acme = db.query(Vendor).filter(Vendor.normalized_name == "acme global supplies").first()
        techflow = db.query(Vendor).filter(Vendor.normalized_name == "techflow solutions").first()

        pos_data = [
            ("PO-501", acme.id if acme else "0", Decimal("23600.00"), "INR"),
            ("PO-502", techflow.id if techflow else "0", Decimal("15000.00"), "INR"),
        ]
        for po_num, v_id, amt, curr in pos_data:
            existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_num).first()
            if not existing:
                po = PurchaseOrder(
                    po_number=po_num,
                    vendor_id=v_id,
                    total_amount=amt,
                    currency=curr,
                    status="open",
                    line_items=[{"description": "IT Hardware and Supplies", "amount": str(amt)}],
                )
                db.add(po)
        db.commit()
        print("Purchase orders seeded.")

        # 4. Business Rules from YAML
        rules = BusinessRuleEngine.load_rules_from_config()
        for r in rules:
            existing = db.query(BusinessRule).filter(BusinessRule.rule_code == r["rule_code"]).first()
            if not existing:
                br = BusinessRule(
                    rule_code=r["rule_code"],
                    name=r["name"],
                    description=r.get("description"),
                    document_type=r.get("document_type", "invoice"),
                    configuration=r.get("configuration", {}),
                    severity=r.get("severity", "high"),
                    enabled=r.get("enabled", True),
                    version=r.get("version", 1),
                )
                db.add(br)
        db.commit()
        print("Business rules synchronized.")

        # 5. Generate sample invoice documents in data/samples
        samples_dir = root_dir / "data" / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)

        inv1_lines = [
            "Vendor: Acme Global Supplies",
            "GSTIN: GSTIN-27AAACA1234A1Z5",
            "Invoice Number: INV-2026-001",
            "Invoice Date: 2026-10-20",
            "Due Date: 2026-11-20",
            "Purchase Order Reference: PO-501",
            "Currency: INR",
            "---",
            "Line Item 1: Cloud Server Maintenance - 20000.00",
            "---",
            "Subtotal: 20000.00",
            "Tax (GST 18%): 3600.00",
            "Total Amount: 23600.00",
        ]
        sample1 = samples_dir / "valid_acme_invoice.pdf"
        create_sample_pdf(sample1, inv1_lines)

        inv2_lines = [
            "Vendor: TechFlow Solutions",
            "GSTIN: GSTIN-07BBBCB5678B2Z1",
            "Invoice Number: INV-2026-002",
            "Invoice Date: 2026-10-22",
            "Due Date: 2026-11-25",
            "Currency: INR",
            "---",
            "Line Item 1: Enterprise Architecture Review - 40000.00",
            "---",
            "Subtotal: 40000.00",
            "Tax: 7200.00",
            "Total Amount: 47200.00",  # Exceeds max automatic amount of 25,000 -> Routes to review!
        ]
        sample2 = samples_dir / "high_amount_review_invoice.pdf"
        create_sample_pdf(sample2, inv2_lines)

        inv3_lines = [
            "Vendor: Unknown Freelancer",
            "Invoice Number: INV-2026-003",
            "Invoice Date: 2026-10-25",
            "Currency: INR",
            "Subtotal: 10000.00",
            "Tax: 1000.00",
            "Total Amount: 15000.00",  # Arithmetic reconciliation mismatch!
        ]
        sample3 = samples_dir / "arithmetic_error_invoice.pdf"
        create_sample_pdf(sample3, inv3_lines)

        sample4 = samples_dir / "scanned_receipt.png"
        create_sample_image(
            sample4,
            [
                "Invoice Number: REC-9921",
                "Vendor: Acme Global Supplies",
                "Date: 2026-10-24",
                "Subtotal: 5000.00",
                "Tax: 900.00",
                "Total Amount: 5900.00",
            ],
        )

        print(f"Generated 4 sample test documents in {samples_dir}.")

        # 6. Ingest samples into document engine and execute pipeline so dashboard is populated!
        print("Ingesting sample documents and running pipeline...")
        for sample_path in [sample1, sample2, sample3, sample4]:
            with open(sample_path, "rb") as f:
                content = f.read()
            doc = IngestionService.ingest_document(
                db=db,
                content=content,
                filename=sample_path.name,
                user_id=None,
            )
            execute_pipeline(doc.id)
            print(f"  Processed {sample_path.name} -> ID: {doc.id}, Status: {doc.status}")

        print("\nSeed demo data completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
