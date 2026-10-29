# System Architecture

## Overview

The AI Document Processing & Decision Engine is an enterprise-grade document operations platform designed to convert unstructured vendor documents (invoices, receipts, purchase orders) into validated, structured data and deterministic business decisions.

```mermaid
flowchart TD
    Client[React Dashboard / REST API Client] --> Ingest[Document Ingestion API]
    Ingest --> Storage[(Local / Object Storage)]
    Ingest --> DB[(PostgreSQL / SQLite)]
    Ingest --> Queue[Asynchronous Celery Queue]

    Queue --> Worker[Celery Worker Engine]
    Worker --> Parser[Document Parser & PyMuPDF]
    Parser --> OCR[Tesseract OCR Engine]
    Parser --> Classifier[Document Classifier]
    Classifier --> Extractor[Structured Extraction Provider]
    Extractor --> Validator[Pydantic & Arithmetic Validator]
    Validator --> Confidence[Confidence Assessor]
    Confidence --> Duplicate[Duplicate & Anomaly Detector]
    Duplicate --> Rules[Deterministic Business Rule Engine]
    Rules --> Decision{Decision Engine}

    Decision -->|Auto-Eligible| Ready[Eligible Pipeline]
    Decision -->|Uncertain / Discrepancy| Review[Human Review Queue]
    Decision -->|Duplicate Blocked| Blocked[Blocked Duplicates]

    Review --> Human[Human Reviewer Workspace]
    Human --> Correct[Field Correction & Revalidation]
    Human --> Approve[Authorized Decision]

    Approve --> Audit[Audit Trail Service]
    Approve --> Webhooks[Retryable HMAC Webhooks]
```

## Core Architectural Principles

1. **Separation of Extraction and Decision Logic**:
   AI and OCR extract data; deterministic Python services validate arithmetic and business rules; explicit policies determine routing; humans handle uncertainty and exceptions.

2. **Immutable Extraction History**:
   Model extractions are stored as immutable `ExtractionResult` records. Reviewer corrections create sequential `ReviewRecord` revisions without overwriting historical extractions.

3. **Asynchronous & Idempotent Processing**:
   Uploads respond immediately with HTTP 202 Accepted. Processing runs in background Celery workers with transaction-safe state transitions.

4. **Auditability**:
   Every state change, reviewer edit, duplicate flag, and webhook delivery attempt is recorded in the `audit_events` ledger.
