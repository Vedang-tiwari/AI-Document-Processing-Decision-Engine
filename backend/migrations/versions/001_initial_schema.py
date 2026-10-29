"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # documents
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("decision_outcome", sa.String(length=50), nullable=True),
        sa.Column("processing_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_documents_file_hash", "documents", ["file_hash"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_created_at", "documents", ["created_at"])
    op.create_index("ix_documents_status_created_at", "documents", ["status", "created_at"])

    # processing_runs
    op.create_table(
        "processing_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("pipeline_version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )
    op.create_index("ix_processing_runs_document_id", "processing_runs", ["document_id"])

    # extraction_results
    op.create_table(
        "extraction_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("processing_run_id", sa.String(length=36), sa.ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schema_version", sa.String(length=50), nullable=False, server_default="1.0.0"),
        sa.Column("extracted_data", sa.JSON(), nullable=False),
        sa.Column("field_evidence", sa.JSON(), nullable=False),
        sa.Column("confidence_data", sa.JSON(), nullable=False),
        sa.Column("validation_results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_extraction_results_document_id", "extraction_results", ["document_id"])
    op.create_index("ix_extraction_results_run_id", "extraction_results", ["processing_run_id"])

    # business_rules
    op.create_table(
        "business_rules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("rule_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("document_type", sa.String(length=50), nullable=False, server_default="invoice"),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="high"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_business_rules_rule_code", "business_rules", ["rule_code"])

    # rule_evaluations
    op.create_table(
        "rule_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("processing_run_id", sa.String(length=36), sa.ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_code", sa.String(length=100), nullable=False),
        sa.Column("rule_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="high"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rule_evaluations_document_id", "rule_evaluations", ["document_id"])
    op.create_index("ix_rule_evaluations_rule_code", "rule_evaluations", ["rule_code"])

    # review_records
    op.create_table(
        "review_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("original_extraction_id", sa.String(length=36), sa.ForeignKey("extraction_results.id"), nullable=True),
        sa.Column("corrected_data", sa.JSON(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_records_document_id", "review_records", ["document_id"])
    op.create_index("ix_review_records_reviewer_id", "review_records", ["reviewer_id"])

    # audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_type", sa.String(length=50), nullable=False, server_default="system"),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_document_id", "audit_events", ["document_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    # webhook_endpoints
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("secret_reference", sa.String(length=255), nullable=False),
        sa.Column("subscribed_events", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # webhook_deliveries
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("endpoint_id", sa.String(length=36), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_http_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_webhook_deliveries_endpoint_id", "webhook_deliveries", ["endpoint_id"])
    op.create_index("ix_webhook_deliveries_event_id", "webhook_deliveries", ["event_id"])

    # vendors
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("tax_id", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vendors_name", "vendors", ["name"])
    op.create_index("ix_vendors_normalized_name", "vendors", ["normalized_name"])
    op.create_index("ix_vendors_tax_id", "vendors", ["tax_id"])

    # purchase_orders
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("po_number", sa.String(length=100), nullable=False, unique=True),
        sa.Column("vendor_id", sa.String(length=36), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column("line_items", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"])
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"])


def downgrade() -> None:
    op.drop_table("purchase_orders")
    op.drop_table("vendors")
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
    op.drop_table("audit_events")
    op.drop_table("review_records")
    op.drop_table("rule_evaluations")
    op.drop_table("business_rules")
    op.drop_table("extraction_results")
    op.drop_table("processing_runs")
    op.drop_table("documents")
    op.drop_table("users")
