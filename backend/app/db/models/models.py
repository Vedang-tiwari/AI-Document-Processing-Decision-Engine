import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    Numeric,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="operator")  # administrator, reviewer, operator
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    reviews = relationship("ReviewRecord", back_populates="reviewer")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    storage_key = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False, default="unknown", index=True)
    status = Column(String(50), nullable=False, default="queued", index=True)
    # queued, processing, review_required, approved, rejected, blocked_duplicate, failed
    decision_outcome = Column(String(50), nullable=True)
    # auto_eligible, review_required, rejected, blocked_duplicate
    processing_attempts = Column(Integer, default=0, nullable=False)
    uploaded_by = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)

    # Relationships
    processing_runs = relationship("ProcessingRun", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("ExtractionResult", back_populates="document", cascade="all, delete-orphan")
    rule_evaluations = relationship("RuleEvaluation", back_populates="document", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="document", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="document")

    __table_args__ = (
        Index("ix_documents_status_created_at", "status", "created_at"),
    )


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    run_number = Column(Integer, nullable=False, default=1)
    pipeline_version = Column(String(50), nullable=False, default="1.0.0")
    status = Column(String(50), nullable=False, default="running")  # running, completed, failed
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="processing_runs")
    extraction = relationship("ExtractionResult", back_populates="processing_run", uselist=False)
    rule_evaluations = relationship("RuleEvaluation", back_populates="processing_run")


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    processing_run_id = Column(String(36), ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    schema_version = Column(String(50), nullable=False, default="1.0.0")
    extracted_data = Column(JSON, nullable=False, default=dict)
    field_evidence = Column(JSON, nullable=False, default=dict)
    confidence_data = Column(JSON, nullable=False, default=dict)
    validation_results = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="extractions")
    processing_run = relationship("ProcessingRun", back_populates="extraction")


class BusinessRule(Base):
    __tablename__ = "business_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=False, default="invoice")
    configuration = Column(JSON, nullable=False, default=dict)
    severity = Column(String(50), nullable=False, default="high")  # critical, high, medium, low
    enabled = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    processing_run_id = Column(String(36), ForeignKey("processing_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(100), nullable=False, index=True)
    rule_version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False)  # passed, failed, warning, skipped
    severity = Column(String(50), nullable=False, default="high")
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="rule_evaluations")
    processing_run = relationship("ProcessingRun", back_populates="rule_evaluations")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)  # corrected, approved, rejected
    original_extraction_id = Column(String(36), ForeignKey("extraction_results.id"), nullable=True)
    corrected_data = Column(JSON, nullable=False, default=dict)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("Document", back_populates="review_records")
    reviewer = relationship("User", back_populates="reviews")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_type = Column(String(50), nullable=False, default="system")  # system, user, worker
    actor_id = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    document = relationship("Document", back_populates="audit_events")


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    secret_reference = Column(String(255), nullable=False)
    subscribed_events = Column(JSON, nullable=False, default=list)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    deliveries = relationship("WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    endpoint_id = Column(String(36), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(50), nullable=False, default="pending")  # pending, delivered, failed
    attempt_count = Column(Integer, default=0, nullable=False)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    last_http_status = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    tax_id = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=False, index=True)
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), nullable=False, default="INR")
    status = Column(String(50), nullable=False, default="open")  # open, closed, matched
    line_items = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
