# AI Document Processing & Decision Engine

An AI-powered document automation platform that converts unstructured business documents into validated, structured data and actionable business decisions. It combines OCR, machine-learning-based classification, LLM-assisted extraction, deterministic business rules, duplicate detection, human-in-the-loop review, asynchronous processing, and auditable decision workflows.

---

## 1. Project Overview

### 1.1 Problem Statement

Businesses receive large volumes of invoices, purchase orders, receipts, contracts, application forms, and other documents. Employees often have to:

- Open and inspect each document manually.
- Re-enter information into business applications.
- Compare invoices against purchase orders and vendor records.
- Identify missing fields, incorrect totals, and inconsistent information.
- Detect duplicate submissions.
- Escalate uncertain cases to supervisors.
- Track approvals and maintain records for audits.

These processes consume time, introduce avoidable errors, and become difficult to manage as document volumes increase.

Traditional OCR can recognize text but does not reliably understand the business meaning of every field. LLMs can extract structured information but may produce incorrect values, misinterpret ambiguous text, or return data that violates business constraints.

A production-oriented solution must combine document understanding with validation, deterministic rules, exception handling, and human oversight.

### 1.2 Proposed Solution

Build a web-based document processing platform that:

1. Accepts documents through a REST API or web dashboard.
2. Validates uploaded files and stores them securely.
3. Processes documents asynchronously.
4. Extracts text using OCR or native document parsing.
5. Classifies each document by type.
6. Extracts structured fields using a configurable extraction pipeline.
7. Validates extracted data against predefined schemas.
8. Calculates field-level and document-level confidence indicators.
9. Executes deterministic business rules.
10. Detects potential duplicates and suspicious anomalies.
11. Routes eligible cases to an automated decision path and uncertain cases to human review.
12. Records corrections, decisions, errors, and processing history.
13. Sends webhook events to external systems.
14. Displays processing status, errors, review queues, and operational metrics.

### 1.3 Primary Use Case

The initial release focuses on **vendor invoice processing with optional purchase-order matching**.

The architecture must support other document types through configurable schemas and extraction adapters, but invoice processing is the primary end-to-end workflow for the MVP.

### 1.4 Target Users

- Accounts payable teams.
- Operations teams.
- Finance administrators.
- Human document reviewers.
- Business application developers integrating through APIs.
- System administrators managing processing rules and integrations.

### 1.5 Business Value

The platform aims to reduce manual data entry, improve processing consistency, surface exceptions earlier, and make document decisions traceable.

It should provide measurable operational metrics, including:

- Total documents received and processed.
- Processing success and failure rates.
- Median and 95th-percentile processing duration.
- Human review rate.
- Field extraction accuracy.
- Duplicate alert rate.
- Webhook delivery success rate.
- Number of documents awaiting review.

Do not claim specific cost savings or accuracy improvements until they have been measured against a representative evaluation dataset.

---

## 2. Project Goals and Non-Goals

### Goals

- Build a complete document-processing lifecycle.
- Support PDF, PNG, and JPEG inputs in the MVP.
- Support digitally generated PDFs and scanned documents.
- Implement OCR and structured extraction.
- Validate data with typed schemas.
- Make business rules configurable.
- Provide duplicate detection and explainable anomaly flags.
- Support human correction and review.
- Process jobs asynchronously.
- Expose versioned REST APIs.
- Provide retryable webhook integrations.
- Maintain an audit trail.
- Build a usable React dashboard.
- Run the complete stack locally using Docker Compose.
- Provide automated tests and reproducible evaluation scripts.

### Non-Goals for the Initial Release

Do not implement these unless the core MVP is complete:

- Fully autonomous payment execution.
- Autonomous contract signing or legally binding approvals.
- Definitive fraud detection.
- Training a custom OCR foundation model.
- Training a custom large language model.
- Complex multi-agent orchestration.
- Kubernetes-based deployment.
- Multi-region distributed processing.
- A general-purpose workflow designer.
- Support for every document format and language.
- Direct integration with numerous ERP or accounting vendors.

The system is a decision-support and document automation platform. It does not replace financial controls or authorized business approval processes.

---

## 3. Technology Stack

Use the following stack unless a repository constraint requires a documented alternative.

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React, TypeScript, Vite | Dashboard and review interface |
| UI styling | Tailwind CSS or existing project styling | Responsive interface |
| Backend | Python, FastAPI | REST APIs and business logic |
| Data validation | Pydantic | Request and extraction schema validation |
| Database | PostgreSQL | Persistent application data |
| ORM/migrations | SQLAlchemy, Alembic | Database access and schema migrations |
| Background jobs | Celery | Asynchronous document processing |
| Queue/broker | Redis | Task queue and transient coordination |
| File storage | Local storage adapter; S3-compatible adapter later | Original documents and artifacts |
| PDF parsing | PyMuPDF or pdfplumber | Native PDF text extraction |
| OCR | Tesseract via pytesseract | Text recognition for scanned pages |
| Image processing | Pillow, optionally OpenCV | Image normalization and preprocessing |
| Classification | Rule-based baseline; Transformers adapter optional | Document-type classification |
| Extraction | Provider-independent structured extraction interface | Field extraction from document text |
| Testing | pytest, HTTPX, Vitest | Backend and frontend testing |
| Containers | Docker, Docker Compose | Reproducible local environment |
| Observability | Python logging, structured events, health checks | Debugging and operational monitoring |

### Model and Provider Strategy

Do not hardwire the entire application to a single LLM provider.

Define a common extraction interface that accepts document text and a document-type schema and returns structured output with supporting evidence.

The initial implementation may use a configurable LLM provider or a deterministic mock provider for local testing. Add a real provider through environment variables and an adapter.

An optional local Transformers-based classifier can be introduced after the baseline pipeline works.

OCR, classification, extraction, validation, and decision-making must remain separate modules.

---

## 4. High-Level Architecture

```mermaid
flowchart TD
    U[React Dashboard / External Client] --> API[FastAPI REST API]

    API --> AUTH[Authentication and Authorization]
    API --> DB[(PostgreSQL)]
    API --> FS[File Storage]
    API --> Q[Redis / Celery Queue]

    Q --> W[Celery Worker]
    W --> ING[File Validation and Text Extraction]
    ING --> OCR[OCR / PDF Parsing]
    OCR --> CLS[Document Classification]
    CLS --> EXT[Structured Field Extraction]
    EXT --> VAL[Schema and Semantic Validation]
    VAL --> CONF[Confidence Assessment]
    CONF --> DUP[Duplicate and Anomaly Checks]
    DUP --> RULES[Business Rule Engine]
    RULES --> DEC{Decision Routing}

    DEC -->|Eligible| AUTO[Automatic Processing Eligible]
    DEC -->|Uncertain or Exception| REVIEW[Human Review Queue]
    DEC -->|Technical Failure| ERR[Retry or Failed State]

    REVIEW --> API
    AUTO --> DB
    REVIEW --> DB
    ERR --> DB

    DB --> AUDIT[Audit Trail]
    DB --> WH[Webhook Dispatcher]
    WH --> EXTAPI[External Business Systems]

    API --> UI[Dashboard and Review UI]
```

### Architectural Principles

1. The API must not perform OCR and LLM extraction synchronously during an upload request.
2. Every accepted document must have a persistent record and a processing status.
3. Original files must remain separate from extracted data.
4. Extraction results must be validated before business rules execute.
5. Business rules must produce explicit outcomes and explanations.
6. Human corrections must not overwrite the historical extraction record.
7. Retryable jobs must be idempotent wherever practical.
8. Database transactions must protect state transitions and review decisions.
9. Every important state transition must be auditable.
10. External webhooks must not block document processing.
11. AI output must be treated as untrusted data.
12. Secrets, document contents, and sensitive personal information must not be written into ordinary application logs.

---

## 5. Core System Components

### 5.1 Document Ingestion Service

Responsibilities:

- Accept PDF, PNG, and JPEG files.
- Enforce configurable file-size limits.
- Verify actual file content rather than trusting the extension alone.
- Reject unsupported formats and malformed files.
- Calculate a cryptographic file hash.
- Generate a unique document identifier.
- Store the original document.
- Persist document metadata.
- Create a background processing job.
- Return the document ID and current status.

The upload endpoint should return HTTP 202 Accepted once the file and processing request have been persisted successfully.

Use a database transaction or a transactional outbox pattern to avoid accepting a document without reliably scheduling its processing.

### 5.2 Document Parsing and OCR Service

Responsibilities:

- Extract native text from digital PDFs.
- Determine whether a page has usable text.
- Run OCR on scanned pages or pages with insufficient text.
- Preserve page numbers and text segments.
- Normalize whitespace and common OCR artifacts.
- Record extraction method and processing errors.

OCR should be page-aware. Do not force every digital PDF through OCR if native text extraction is adequate.

Store OCR artifacts separately from the original file.

### 5.3 Document Classification Service

Initial document types:

- `invoice`
- `purchase_order`
- `receipt`
- `contract`
- `unknown`

Start with a simple, testable classification baseline using document text, headings, and configurable patterns. Provide an interface for a trained Transformer classifier later.

Classification output must contain:

- Predicted document type.
- Model or classifier identifier.
- Optional score.
- Classification warnings.

Unknown or ambiguous documents must be routed to manual classification or a controlled failure path. Do not force every document into a known category.

### 5.4 Structured Extraction Service

The extraction service converts document text into structured data according to a document-type-specific schema.

For invoices, extract:

- Supplier name.
- Supplier tax identifier, when present.
- Invoice number.
- Invoice date.
- Due date, when present.
- Currency.
- Subtotal.
- Tax amount.
- Total amount.
- Purchase order reference, when present.
- Line items, when available.

Each extracted field should retain:

- The extracted value.
- The supporting text or evidence reference, when available.
- Source page or text segment, when available.
- Extraction method.
- Field-level confidence indicator, when available.

The extraction model must return schema-constrained data. Validate its output using Pydantic.

Do not invent missing values. Represent absent optional fields as null and record missing required fields as validation issues.

Do not treat an LLM's self-reported confidence as a calibrated probability. Use evidence coverage, OCR quality, validation results, and evaluated model behavior to build a confidence assessment.

### 5.5 Validation Service

Validation occurs in multiple stages.

**Structural validation**

- Required fields exist.
- Data types are correct.
- Dates use supported formats.
- Amounts are valid decimal values.
- Currency codes are supported.
- Line items follow the expected schema.

**Semantic validation**

- Invoice date is plausible.
- Total amounts are non-negative where appropriate.
- Due dates are not earlier than invoice dates unless explicitly allowed.
- Tax and subtotal values are consistent with the invoice total within configured rounding tolerances.
- Required supplier identifiers are present where the configured policy requires them.

Validation must produce structured issues with codes, severity, field paths, and explanations.

A validation failure should not silently discard the extraction result.

### 5.6 Confidence Assessment Service

Confidence must be assessed at both field and document levels.

Possible signals:

- OCR quality.
- Whether a field has supporting evidence.
- Extraction-provider confidence, if available and evaluated.
- Schema validation results.
- Cross-field consistency.
- Classification ambiguity.
- Missing required fields.

Store the signals and reasons that contributed to the assessment.

Example:

```json
{
  "document_score": 0.91,
  "assessment": "high",
  "signals": {
    "required_fields_present": true,
    "schema_valid": true,
    "evidence_coverage": 0.95,
    "cross_field_consistency": true
  },
  "reasons": []
}
```

This is an illustrative contract, not a calibrated score formula.

A production implementation must document its scoring formula and calibrate thresholds against labeled examples.

A high confidence score does not override a failed hard business rule, a suspected duplicate, or a required human approval.

### 5.7 Business Rule Engine

Implement business rules as deterministic, testable application code or declarative configuration.

Initial rules:

- Required invoice fields must be present.
- Supplier must exist in the configured vendor registry.
- Duplicate invoice checks must pass.
- Invoice total must reconcile with subtotal and tax within configured tolerance.
- Invoice amount must not exceed the applicable automatic-processing limit.
- Purchase order references must exist when purchase-order matching is required.
- Invoice totals must match purchase order amounts within configured tolerance.
- Documents with critical validation errors must be reviewed.
- Documents with unresolved anomalies must not be automatically approved.

Each rule execution should return:

```json
{
  "rule_code": "INVOICE_TOTAL_RECONCILIATION",
  "status": "failed",
  "severity": "high",
  "message": "Invoice total does not reconcile with subtotal and tax.",
  "field_paths": ["subtotal", "tax_amount", "total_amount"]
}
```

Rule results must be stored with the document decision.

Support rule configuration for thresholds, tolerances, and required checks. Do not execute arbitrary Python code supplied by users.

### 5.8 Duplicate and Anomaly Detection

Implement two separate mechanisms.

**Exact duplicate detection**

Use document hashes to identify byte-identical files. A repeated upload may still need to create a submission record, but it should not accidentally trigger duplicate financial processing.

**Business duplicate detection**

Use normalized business identifiers, including:

- Supplier identity.
- Invoice number.
- Invoice date.
- Currency.
- Total amount.

Apply database uniqueness constraints or transaction-safe duplicate checks to prevent concurrent workers from processing the same invoice twice.

**Potential anomaly detection**

Flag conditions such as:

- Same supplier and invoice number with conflicting totals.
- Unusually high invoice amounts.
- Unexpected supplier changes.
- Repeated near-duplicate submissions.
- Large differences between an invoice and its purchase order.

For the MVP, use explainable rules and historical comparisons rather than a complex unsupervised ML system.

An anomaly is a review signal, not proof of fraud. Store the reason and supporting records.

### 5.9 Decision Service

The decision service combines extraction validity, confidence assessment, duplicate checks, business-rule results, and applicable approval policies.

Possible decision outcomes:

- `auto_eligible`
- `review_required`
- `rejected`
- `blocked_duplicate`

`auto_eligible` means the document passed the configured automated checks. It does not mean a payment was executed or that an external financial system accepted the invoice.

`rejected` should represent a business decision under an explicit policy, not merely an OCR or model failure.

`blocked_duplicate` means the submission is prevented from proceeding through the normal processing path because it matches an existing record under the duplicate policy.

Technical failures should use processing statuses rather than being misrepresented as business rejections.

### 5.10 Human Review Service

Reviewers must be able to:

- View a document and its extracted fields.
- Inspect supporting evidence and validation issues.
- Correct extracted values.
- Add a reason or review comment.
- Approve, reject, or request further information where supported.
- View prior extraction results and corrections.
- View the rules that influenced the decision.

A reviewer correction must create a new review revision or correction record. Preserve the original model output.

Enforce reviewer permissions on the server. A frontend-only disabled button is not an authorization control.

### 5.11 Audit Trail Service

Record important events:

- Document uploaded.
- Processing job started.
- OCR completed.
- Classification completed.
- Extraction completed.
- Validation completed.
- Business rules evaluated.
- Decision generated.
- Document routed to review.
- Reviewer corrected fields.
- Reviewer approved or rejected.
- Webhook delivery attempted.
- Processing failed or was retried.

Each audit event should contain an event ID, document ID, timestamp, actor or service identity, action, and relevant structured metadata.

Never place passwords, API keys, full document contents, or unnecessary personal information in audit metadata.

### 5.12 Webhook Service

Allow authenticated clients to register webhook endpoints for events such as:

- `document.processing_completed`
- `document.review_required`
- `document.processing_failed`
- `document.review_completed`

Webhook payloads should contain identifiers, statuses, decision summaries, and timestamps. Avoid sending full document contents by default.

Requirements:

- Signed webhook payloads using HMAC.
- Configurable delivery timeout.
- Retry policy with exponential backoff.
- Delivery attempt records.
- Idempotency or event identifiers.
- Manual retry for authorized administrators.
- Protection against unsafe internal network destinations and server-side request forgery.

Webhook failures must not roll back completed document processing.

---

## 6. End-to-End Processing Workflow

### Phase 1: Upload

1. The client submits a document.
2. The API authenticates the request and checks permissions.
3. The file is validated and stored.
4. A document record and processing request are persisted.
5. A background task is scheduled.
6. The API returns the document ID and status.

### Phase 2: Parsing and Classification

1. The worker retrieves the document.
2. The worker checks the current processing state.
3. Native text extraction is attempted where applicable.
4. OCR is used when required.
5. Text artifacts and parsing metadata are saved.
6. The classifier predicts a document type.
7. Unsupported or ambiguous types are routed to review or a controlled failure state.

### Phase 3: Extraction and Validation

1. The worker loads the schema for the document type.
2. The extraction provider receives the relevant document text.
3. The result is validated against the schema.
4. Field-level evidence and extraction metadata are recorded.
5. Semantic validation rules execute.
6. Confidence indicators are calculated.
7. Failed fields and validation issues are persisted.

### Phase 4: Duplicate Detection and Business Evaluation

1. The system checks for exact file duplicates.
2. The system checks business identifiers against existing records.
3. Applicable anomaly checks execute.
4. Business rules evaluate the validated extraction.
5. The decision service determines the next state.
6. Decision explanations and rule results are persisted.

### Phase 5: Routing

- Eligible documents move to the configured automatic-processing outcome.
- Uncertain documents move to the human review queue.
- Duplicate submissions are blocked or linked to the original record.
- Technical failures are retried when safe and eventually recorded as failed if retries are exhausted.

### Phase 6: Review

1. A reviewer opens the document.
2. The reviewer inspects extracted fields and supporting evidence.
3. The reviewer corrects fields where necessary.
4. Validation and business rules execute again against the corrected data.
5. The reviewer makes an authorized decision.
6. The system records the reviewer, decision, corrections, and timestamp.
7. The final status and webhook events are updated.

### Phase 7: Integration and Monitoring

1. Events are placed into the webhook delivery queue.
2. Webhooks are delivered independently of the document-processing worker.
3. Delivery attempts and outcomes are recorded.
4. The dashboard reflects the latest processing and review states.

---

## 7. Document Lifecycle and State Machine

Use a finite set of well-defined statuses.

| Status | Meaning |
|---|---|
| `queued` | Accepted and awaiting processing |
| `processing` | A worker is actively processing the document |
| `review_required` | Human intervention is required |
| `approved` | Authorized final approval has been recorded |
| `rejected` | An authorized final rejection has been recorded |
| `blocked_duplicate` | The submission is blocked by duplicate policy |
| `failed` | Processing failed after the retry policy was exhausted |

The business decision `auto_eligible` is a decision outcome, not a final approval status. If the MVP does not perform actual downstream approval, an eligible document should remain available for authorized review or integration instead of being falsely marked as financially approved.

### Allowed transitions

- `queued` → `processing`
- `processing` → `review_required`
- `processing` → `approved` only when the configured policy explicitly permits automatic approval
- `processing` → `rejected` only when the configured policy supports automatic rejection
- `processing` → `blocked_duplicate`
- `processing` → `failed`
- `failed` → `queued` through an authorized retry
- `review_required` → `processing` when a correction requires reevaluation
- `review_required` → `approved`
- `review_required` → `rejected`

Store each transition with its actor, timestamp, reason, and previous/new state.

Enforce transitions in the backend. Reject invalid transitions with HTTP 409 Conflict.

A task retry must not create duplicate approvals, audit events that falsely imply multiple decisions, or repeated downstream side effects.

---

## 8. Database Design

Use PostgreSQL with SQLAlchemy and Alembic migrations.

### 8.1 `users`

- `id`: UUID primary key
- `email`: unique
- `password_hash`: nullable when using external identity management
- `role`: administrator, reviewer, or operator
- `is_active`: boolean
- `created_at`
- `updated_at`

### 8.2 `documents`

- `id`: UUID primary key
- `original_filename`
- `mime_type`
- `file_size_bytes`
- `file_hash`
- `storage_key`
- `document_type`
- `status`
- `processing_attempts`
- `uploaded_by`: user ID or API client identity
- `created_at`
- `updated_at`
- `completed_at`: nullable
- `failure_code`: nullable
- `failure_message`: nullable and sanitized

Index status, document type, creation timestamp, and normalized business identifiers where applicable.

### 8.3 `processing_runs`

- `id`: UUID primary key
- `document_id`: foreign key
- `run_number`
- `pipeline_version`
- `status`
- `started_at`
- `completed_at`
- `error_code`
- `error_message`
- `duration_ms`

A document may have multiple processing runs. Preserve previous runs for debugging and reproducibility.

### 8.4 `extraction_results`

- `id`: UUID primary key
- `document_id`: foreign key
- `processing_run_id`: foreign key
- `schema_version`
- `extracted_data`: JSONB
- `field_evidence`: JSONB
- `confidence_data`: JSONB
- `validation_results`: JSONB
- `created_at`

Treat extraction results as immutable records.

### 8.5 `business_rules`

- `id`: UUID primary key
- `rule_code`: unique
- `name`
- `description`
- `document_type`
- `configuration`: JSONB
- `severity`
- `enabled`
- `version`
- `created_at`
- `updated_at`

### 8.6 `rule_evaluations`

- `id`: UUID primary key
- `document_id`: foreign key
- `processing_run_id`: foreign key
- `rule_code`
- `rule_version`
- `status`
- `severity`
- `message`
- `details`: JSONB
- `created_at`

### 8.7 `review_records`

- `id`: UUID primary key
- `document_id`: foreign key
- `reviewer_id`: foreign key
- `action`
- `original_extraction_id`: foreign key
- `corrected_data`: JSONB
- `comment`
- `created_at`

Preserve each review action rather than overwriting history.

### 8.8 `audit_events`

- `id`: UUID primary key
- `document_id`: nullable foreign key
- `actor_type`
- `actor_id`: nullable
- `event_type`
- `metadata`: JSONB
- `created_at`

Application-level protections should prevent ordinary users from editing or deleting historical audit records.

### 8.9 `webhook_endpoints`

- `id`: UUID primary key
- `name`
- `url`
- `secret_reference`
- `subscribed_events`: JSONB
- `enabled`
- `created_at`
- `updated_at`

Do not return webhook secrets in API responses.

### 8.10 `webhook_deliveries`

- `id`: UUID primary key
- `endpoint_id`: foreign key
- `event_id`
- `event_type`
- `payload`: JSONB
- `status`
- `attempt_count`
- `next_attempt_at`
- `last_http_status`
- `last_error`
- `created_at`
- `delivered_at`

Use database constraints and transactions to protect event uniqueness and prevent concurrent duplicate business processing.

### 8.11 Vendor and Purchase Order Records

Create simple reference tables for `vendors` and `purchase_orders`.

The vendor table should contain a stable ID, normalized supplier name, optional tax identifier, and active status.

Purchase orders should include a reference number, vendor ID, total amount, currency, status, and optional line-item details.

These tables provide reference data for invoice validation and purchase-order matching. Do not build a full ERP system.

---

## 9. Extraction Schemas

### 9.1 Invoice Extraction Example

```json
{
  "document_type": "invoice",
  "supplier": {
    "name": "Example Supplies Pvt Ltd",
    "tax_id": null
  },
  "invoice_number": "INV-1042",
  "invoice_date": "2026-10-20",
  "due_date": "2026-11-19",
  "currency": "INR",
  "subtotal": "41000.00",
  "tax_amount": "7500.00",
  "total_amount": "48500.00",
  "purchase_order_reference": "PO-501",
  "line_items": []
}
```

This is illustrative test data, not an actual invoice.

### Extraction Requirements

- Represent monetary values as decimal strings at API boundaries.
- Avoid binary floating-point arithmetic for financial calculations.
- Use ISO-formatted dates.
- Represent missing optional values as null.
- Define required fields in versioned Pydantic schemas.
- Preserve evidence separately from normalized field values.
- Validate the arithmetic relationship between subtotal, tax, and total.
- Allow configurable rounding tolerances.
- Store schema and pipeline versions with each extraction.

### Evidence Example

```json
{
  "invoice_number": {
    "value": "INV-1042",
    "page": 1,
    "evidence_text": "Invoice No: INV-1042",
    "source": "ocr",
    "confidence": 0.96
  }
}
```

The evidence confidence above is illustrative. The implementation must document the source and interpretation of every confidence value.

If evidence cannot be located, record that limitation rather than fabricating a page number or quote.

---

## 10. Confidence and Decision Policy

Use configurable thresholds rather than scattering hardcoded numbers throughout the codebase.

Example initial configuration:

```yaml
confidence:
  automatic_processing_threshold: 0.90
  review_threshold: 0.70

processing:
  maximum_attempts: 3
  retry_backoff_seconds: [5, 30, 120]

documents:
  maximum_file_size_mb: 20
  supported_types:
    - application/pdf
    - image/png
    - image/jpeg

invoice:
  require_vendor_match: true
  require_purchase_order_match: false
  maximum_automatic_amount: "25000.00"
  currency: "INR"
  amount_tolerance: "1.00"
```

These values are starter settings for development, not validated financial policy. The implementation must allow configuration through a documented settings layer and validate configuration at startup.

A decision policy should evaluate conditions in this order:

1. Technical processing must have completed.
2. The document type must be supported.
3. Required extraction fields must be present.
4. Schema and semantic validation must pass.
5. No blocking duplicate condition may exist.
6. Required vendor and purchase-order checks must pass.
7. No unresolved critical anomaly may exist.
8. Confidence must satisfy the configured threshold.
9. Any amount limit or approval requirement must pass.
10. The resulting outcome must comply with the configured human-approval policy.

If any required condition fails, route the document to review or the explicitly configured blocking path.

Do not automatically approve a document merely because its confidence score is high.

---

## 11. REST API Specification

Use the `/api/v1` prefix, typed request/response schemas, consistent error formats, and pagination for collection endpoints.

### Document APIs

#### `POST /api/v1/documents`

Upload a document using multipart form data.

Request fields:

- `file`: required file
- `document_type`: optional expected type
- `metadata`: optional validated metadata

Response: `202 Accepted`

```json
{
  "document_id": "uuid",
  "status": "queued",
  "message": "Document accepted for processing."
}
```

#### `GET /api/v1/documents`

List documents with pagination and optional filters:

- `status`
- `document_type`
- `created_from`
- `created_to`
- `page`
- `page_size`

#### `GET /api/v1/documents/{document_id}`

Return document metadata, status, latest decision, and relevant processing summary.

#### `GET /api/v1/documents/{document_id}/results`

Return extraction data, validation results, confidence signals, and decision explanations.

#### `GET /api/v1/documents/{document_id}/file`

Return an authorized file response or a short-lived signed URL, depending on the storage adapter.

#### `POST /api/v1/documents/{document_id}/retry`

Retry an eligible failed document.

The endpoint must prevent duplicate active jobs and require appropriate permissions.

### Review APIs

#### `GET /api/v1/reviews`

Return the human review queue with pagination and filters.

#### `GET /api/v1/reviews/{document_id}`

Return the document, extracted fields, evidence, validation issues, and prior review history.

#### `POST /api/v1/reviews/{document_id}/correct`

Accept reviewer corrections.

```json
{
  "corrections": {
    "invoice_number": "INV-1042",
    "total_amount": "48500.00"
  },
  "comment": "Corrected invoice number after inspecting the source."
}
```

Validate all corrected fields. Record a new revision, rerun applicable validation and rules, and preserve the original extraction.

#### `POST /api/v1/reviews/{document_id}/decision`

Accept an authorized reviewer decision.

```json
{
  "decision": "approved",
  "comment": "Verified against the invoice and supporting records."
}
```

Allowed values must be validated against the review workflow. A reviewer must not approve a document that violates mandatory system constraints unless an explicit, authorized exception policy exists.

### Rule APIs

- `GET /api/v1/rules`
- `GET /api/v1/rules/{rule_id}`
- `PATCH /api/v1/rules/{rule_id}`

Rule modifications must be authorized, validated, versioned, and audited.

### Webhook APIs

- `POST /api/v1/webhooks`
- `GET /api/v1/webhooks`
- `PATCH /api/v1/webhooks/{webhook_id}`
- `DELETE /api/v1/webhooks/{webhook_id}`
- `GET /api/v1/webhooks/{webhook_id}/deliveries`
- `POST /api/v1/webhooks/{webhook_id}/deliveries/{delivery_id}/retry`

Webhook administration must be restricted to authorized users.

### Dashboard APIs

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/processing-metrics`
- `GET /api/v1/dashboard/recent-errors`

Return aggregate counts, processing durations, review counts, and error summaries.

### API Error Format

Use a consistent error structure:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document does not exist.",
    "request_id": "uuid"
  }
}
```

Use appropriate HTTP status codes:

- `400`: malformed request
- `401`: unauthenticated
- `403`: unauthorized
- `404`: resource not found
- `409`: invalid state transition or conflicting operation
- `413`: file too large
- `415`: unsupported media type
- `422`: request or schema validation failure
- `429`: rate limit exceeded
- `500`: unexpected server failure

Document all endpoints in the OpenAPI specification generated by FastAPI.

---

## 12. Authentication and Authorization

Implement authentication before exposing document and review APIs.

For the MVP, use secure session-based authentication or a documented JWT implementation. Use an established password-hashing library if password authentication is implemented.

Roles:

**Administrator**
- Manage users and system configuration.
- Manage rules and webhook endpoints.
- View operational metrics and audit events.
- Retry eligible failed jobs.

**Reviewer**
- Access assigned or permitted documents.
- Correct extraction fields.
- Make authorized review decisions.
- View relevant evidence and history.

**Operator**
- Upload and inspect permitted documents.
- Monitor processing.
- View results according to permissions.

The backend must enforce access control on every protected endpoint.

Design document ownership and organization boundaries explicitly. If multi-tenancy is implemented, every document query, file access, review, and webhook operation must enforce tenant isolation. Do not treat a tenant ID supplied by a client as proof of authorization.

Protect against unauthorized file access, brute-force login attempts, insecure file uploads, and accidental exposure of document data.

---

## 13. Frontend Dashboard Requirements

Build a clean, responsive React and TypeScript application.

### 13.1 Overview Dashboard

Display:

- Total documents.
- Queued documents.
- Documents processing.
- Documents awaiting review.
- Approved and rejected documents.
- Failed jobs.
- Recent processing activity.
- Processing duration and failure trends.

Use real backend data. Do not leave production-looking mock metrics connected to the actual application workflow.

### 13.2 Document Upload

Provide:

- Drag-and-drop upload.
- File picker.
- File type and size validation.
- Upload progress.
- Success and failure states.
- Document status after submission.
- Link to the document detail page.

### 13.3 Document List

Include:

- Document name.
- Document type.
- Upload timestamp.
- Current status.
- Supplier or invoice identifier when available.
- Confidence indicator.
- Processing duration.
- Search, sorting, filtering, and pagination.

### 13.4 Document Detail

Display:

- Document metadata.
- Original file preview where supported.
- Extracted fields.
- Field-level evidence.
- Validation issues.
- Business rule outcomes.
- Duplicate or anomaly warnings.
- Processing history.
- Audit events.
- Latest decision and explanation.

### 13.5 Human Review Workspace

Provide a side-by-side document viewer and editable extraction form.

Reviewers should be able to:

- Inspect the original document.
- Correct extracted values.
- See required fields and validation errors.
- Inspect rule failures.
- Add a review comment.
- Submit an authorized decision.
- View previous revisions.

Require confirmation for consequential actions. Clearly distinguish saving corrections from making a final approval decision.

### 13.6 Settings and Integrations

Provide administrative screens for:

- Business rule configuration.
- Processing thresholds.
- Webhook registration.
- Webhook delivery history.
- User management where implemented.

Do not display webhook signing secrets after initial creation.

### Frontend Quality Requirements

- Typed API client.
- Centralized error handling.
- Loading, empty, and error states.
- Responsive layout.
- Accessible forms and controls.
- No hardcoded backend URLs outside configuration.
- No direct database access from the browser.
- No secrets embedded in frontend code.

---

## 14. Repository Structure

Use a modular monolith for the MVP. Do not split the application into microservices prematurely.

```text
ai-document-decision-engine/
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── alembic.ini
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   └── exceptions.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── documents.py
│   │   │       ├── reviews.py
│   │   │       ├── rules.py
│   │   │       ├── webhooks.py
│   │   │       └── dashboard.py
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── base.py
│   │   │   └── models/
│   │   ├── schemas/
│   │   │   ├── document.py
│   │   │   ├── invoice.py
│   │   │   ├── review.py
│   │   │   └── webhook.py
│   │   ├── services/
│   │   │   ├── ingestion.py
│   │   │   ├── document_parser.py
│   │   │   ├── ocr.py
│   │   │   ├── classification.py
│   │   │   ├── extraction.py
│   │   │   ├── validation.py
│   │   │   ├── confidence.py
│   │   │   ├── duplicate_detection.py
│   │   │   ├── anomaly_detection.py
│   │   │   ├── business_rules.py
│   │   │   ├── decision_engine.py
│   │   │   ├── review.py
│   │   │   ├── audit.py
│   │   │   └── webhooks.py
│   │   ├── tasks/
│   │   │   ├── celery_app.py
│   │   │   ├── document_tasks.py
│   │   │   └── webhook_tasks.py
│   │   └── storage/
│   │       ├── base.py
│   │       └── local.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/
│   └── migrations/
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   ├── documents/
│   │   │   ├── reviews/
│   │   │   ├── rules/
│   │   │   └── webhooks/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── types/
│   │   └── main.tsx
│   └── tests/
│
├── configs/
│   ├── settings.yaml
│   └── business_rules.yaml
│
├── data/
│   ├── samples/
│   └── evaluation/
│
├── scripts/
│   ├── seed_demo_data.py
│   └── evaluate_extraction.py
│
└── docs/
    ├── architecture.md
    ├── api.md
    ├── security.md
    └── evaluation.md
```

Adapt this structure to the repository if it already exists. Do not duplicate equivalent modules merely to match this tree.

---

## 15. Environment Configuration

Provide a `.env.example` with documented variables.

```dotenv
APP_ENV=development
APP_NAME=AI Document Processing & Decision Engine
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://app:app@postgres:5432/documents
REDIS_URL=redis://redis:6379/0

STORAGE_BACKEND=local
STORAGE_PATH=/app/storage
MAX_FILE_SIZE_MB=20

OCR_LANGUAGE=eng
OCR_TIMEOUT_SECONDS=60

EXTRACTION_PROVIDER=mock
LLM_API_KEY=
LLM_MODEL=

CONFIDENCE_AUTO_THRESHOLD=0.90
CONFIDENCE_REVIEW_THRESHOLD=0.70

MAX_PROCESSING_ATTEMPTS=3
WEBHOOK_TIMEOUT_SECONDS=10

LOG_LEVEL=INFO
```

These are example development settings. The implementation must provide a documented way to configure the authentication secret, database credentials, webhook signing keys, and any external provider credentials.

Never commit a populated `.env` file, real API keys, or production secrets.

Use separate development and production configuration. Validate required settings at startup and fail clearly when a required secret is missing.

---

## 16. Asynchronous Processing and Reliability

Use Celery workers to execute document processing outside the request-response cycle.

### Requirements

- Separate API and worker processes.
- Persistent processing status.
- Bounded retries with exponential backoff.
- Explicit retryable and non-retryable error classification.
- Job timeout handling.
- Idempotent task execution.
- Database-backed processing-run records.
- Controlled concurrent processing.
- Dead-letter or exhausted-task visibility.
- Health checks for API, database, Redis, and worker.
- Graceful shutdown where practical.

Do not assume that Celery provides exactly-once execution. Tasks can run more than once.

Use unique processing-run identifiers, state checks, database constraints, and transaction-safe updates to make repeated execution safe.

A worker should not mark a document as failed for a temporary provider timeout if a retry remains available.

Store sanitized error codes and messages. Avoid persisting full prompts or entire document text in exception messages.

---

## 17. Security and Data Privacy

Treat every uploaded document and extracted value as untrusted input.

Implement:

- File size and file type restrictions.
- Actual file-content validation.
- Secure filename handling.
- Randomized storage keys.
- Access-controlled file retrieval.
- Authentication and authorization.
- Rate limiting on sensitive endpoints.
- Secure secret management.
- Database parameterization through the ORM.
- Input validation for all API payloads.
- Protection against malicious document content and prompt injection.
- Webhook URL validation and SSRF protections.
- Restricted outbound network access where feasible.
- Safe error messages.
- Configurable retention and deletion policies.
- Redaction of sensitive values in logs.
- Backup and recovery guidance.

Never execute instructions found inside uploaded documents. Document contents are data, not trusted system instructions.

The extraction model must not be allowed to invoke tools, access secrets, modify business rules, or directly approve transactions.

Enforce any financial approval policy in deterministic backend code.

---

## 18. Observability and Monitoring

Implement structured logs and consistent correlation IDs.

Record:

- Request ID.
- Document ID.
- Processing-run ID.
- Task ID.
- Pipeline stage.
- Stage duration.
- Error code.
- Retry count.
- Provider identifier.
- Final routing outcome.

Do not log raw document contents or sensitive extracted fields by default.

Expose health endpoints:

- `GET /health/live`
- `GET /health/ready`

Liveness indicates whether the application process is running. Readiness should verify that required dependencies are available.

Track the following metrics:

- Documents uploaded per hour.
- Queue waiting time.
- Processing duration by stage.
- Extraction and validation failure rates.
- Retry and terminal failure rates.
- Review queue size and age.
- Webhook delivery success rate.
- Duplicate alert frequency.

Keep operational health checks separate from business dashboard metrics.

---

## 19. Testing Strategy

### Unit Tests

Test each module independently.

Examples:

- File validation.
- PDF text extraction.
- OCR fallback behavior.
- Document classification.
- Pydantic schema validation.
- Monetary arithmetic and rounding.
- Confidence assessment.
- Duplicate matching.
- Business rule evaluation.
- Decision routing.
- State transition validation.
- Webhook signing.
- Retry eligibility.

### Integration Tests

Test interactions between:

- FastAPI and PostgreSQL.
- API upload and file storage.
- Upload endpoint and task queue.
- Celery worker and extraction service.
- Extraction results and business rules.
- Human corrections and audit records.
- Webhook events and delivery records.

Use disposable test databases and mock external services where appropriate.

### End-to-End Tests

At minimum, implement these scenarios:

**Scenario A: Valid invoice**

- Upload a valid invoice.
- Confirm the job is queued.
- Confirm extraction and validation complete.
- Confirm the decision is consistent with configured rules.
- Confirm the result appears in the dashboard.

**Scenario B: Low-quality scan**

- Upload a poorly scanned invoice.
- Confirm OCR issues are captured.
- Confirm missing or uncertain required fields trigger review.
- Confirm the original document remains accessible to authorized reviewers.

**Scenario C: Duplicate invoice**

- Upload the same file twice.
- Confirm the duplicate policy prevents accidental duplicate financial processing.
- Confirm both submission attempts can be traced.

**Scenario D: Business-rule failure**

- Upload an invoice with a mismatched total.
- Confirm the rule failure is explained.
- Confirm the document cannot bypass the required review policy.

**Scenario E: Human correction**

- Open a document requiring review.
- Correct an extracted field.
- Confirm the correction is validated.
- Confirm the original extraction is preserved.
- Confirm the reviewer action is recorded in the audit trail.

**Scenario F: Transient provider failure**

- Simulate a temporary extraction-provider timeout.
- Confirm the task retries.
- Confirm the job does not create duplicate business records.

**Scenario G: Webhook failure**

- Simulate a webhook endpoint timeout.
- Confirm processing completes independently.
- Confirm delivery retries are scheduled.
- Confirm delivery history records the outcome.

**Scenario H: Unauthorized access**

- Attempt to access a document without the required permissions.
- Confirm the API denies access.
- Confirm unauthorized file retrieval is prevented.

---

## 20. AI Evaluation Framework

Do not evaluate the project only by whether it returns JSON.

Create a small labeled dataset of representative invoice documents, including:

- Digital PDFs.
- Scanned PDFs.
- Different layouts.
- Missing fields.
- Poor image quality.
- Tax and total inconsistencies.
- Duplicate invoices.
- Unusual but valid cases.

Store expected extraction results in a controlled evaluation dataset.

Measure:

### Extraction quality

- Exact-match accuracy for invoice number.
- Date extraction accuracy.
- Supplier identification accuracy.
- Monetary field accuracy.
- Required-field completeness.
- Line-item extraction accuracy when supported.

Normalize values carefully before comparison. For example, `48500`, `48500.00`, and `48,500.00` may represent the same amount.

### Classification quality

- Per-class precision and recall.
- Macro F1 score.
- Unknown-document detection performance.

### Decision quality

- Automatic-processing precision.
- Percentage of documents routed to review.
- Rate of critical validation failures missed.
- False duplicate alert rate.
- Reviewer correction rate.

### Operational quality

- Median and p95 processing duration.
- Processing failure rate.
- Retry rate.
- Webhook delivery latency.

Report metrics alongside the evaluation dataset size, test conditions, and model/provider version.

Do not tune confidence thresholds on the final evaluation set. Use a separate validation set for threshold calibration.

---

## 21. Local Development and Setup

Prerequisites:

- Git.
- Docker and Docker Compose.
- Python version supported by the chosen dependencies.
- Node.js version supported by the frontend.
- Tesseract OCR installed in the worker image.
- An LLM provider key only if a real external extraction provider is enabled.

### Start the Infrastructure

```bash
git clone <repository-url>
cd ai-document-decision-engine
```

Copy `.env.example` to `.env` and configure development settings.

Start the services:

```bash
docker compose up --build -d
```

Run database migrations:

```bash
docker compose exec api alembic upgrade head
```

The exact service names must match `docker-compose.yml`.

Initialize demo data using a documented seed command.

Open the frontend and FastAPI documentation using the addresses configured in Docker Compose.

For a local Python development workflow, document how to:

1. Create a virtual environment.
2. Install project dependencies.
3. Configure PostgreSQL and Redis.
4. Install OCR dependencies.
5. Run Alembic migrations.
6. Start the FastAPI server.
7. Start the Celery worker.
8. Start the React development server.
9. Execute the test suite.

Provide explicit PowerShell-compatible commands in the documentation where Windows support is intended.

Do not claim the stack works until the documented commands have been tested.

---

## 22. Deployment Strategy

The MVP should run as a containerized application.

Required services:

- React frontend.
- FastAPI API server.
- Celery worker.
- PostgreSQL.
- Redis.

File storage may use a persistent local volume for development. Production deployments should use durable object storage and appropriate access controls.

Deployment requirements:

- Environment-based configuration.
- Database migrations.
- Health checks.
- Persistent storage.
- Secret management.
- HTTPS termination.
- Database backups.
- Log collection.
- Resource limits.
- Worker concurrency configuration.
- Recovery instructions.

Document the deployment process and required environment variables.

Do not introduce Kubernetes, service meshes, or distributed tracing infrastructure unless the core platform is complete and there is a concrete need.

---

## 23. Implementation Plan

Implement the project incrementally. Keep the repository runnable after each phase.

### Phase 1: Foundation

- Initialize backend and frontend.
- Configure PostgreSQL and Redis.
- Add SQLAlchemy models and Alembic.
- Configure FastAPI and React.
- Add Docker Compose.
- Implement health endpoints.
- Establish structured logging and configuration.

**Acceptance criteria:** All core services start locally, migrations run, and the API is reachable.

### Phase 2: Upload and Document Lifecycle

- Implement secure file upload.
- Validate supported formats and size limits.
- Add file hashing and storage.
- Persist document metadata.
- Implement status transitions.
- Add Celery processing tasks.
- Display uploaded documents in the dashboard.

**Acceptance criteria:** An upload creates a persistent document record and an asynchronous processing job.

### Phase 3: Parsing, OCR, and Classification

- Implement native PDF parsing.
- Implement OCR fallback.
- Persist text artifacts and errors.
- Add baseline document classification.
- Add an unknown-document path.

**Acceptance criteria:** Digital PDFs and scanned samples can be processed, and unsupported document types are handled explicitly.

### Phase 4: Extraction and Validation

- Define versioned extraction schemas.
- Implement the provider interface.
- Implement the mock extraction provider for deterministic tests.
- Add the configured real extraction provider.
- Implement field evidence and validation.
- Add confidence assessment.

**Acceptance criteria:** Extraction results are typed, persisted, explainable, and validated.

### Phase 5: Business Decisions

- Implement vendor reference data.
- Add invoice validation rules.
- Implement duplicate detection.
- Add anomaly flags.
- Implement decision routing.
- Persist rule evaluations and explanations.

**Acceptance criteria:** Valid, invalid, duplicate, and uncertain cases produce the correct configured outcomes.

### Phase 6: Human Review

- Build the review queue.
- Add document preview and extracted-field editing.
- Implement reviewer decisions.
- Preserve original extraction results.
- Add audit events and authorization.

**Acceptance criteria:** A reviewer can correct an extraction, revalidate it, and make an authorized decision without losing history.

### Phase 7: Integrations and Reliability

- Add webhook registration.
- Implement event delivery and HMAC signing.
- Add retries and delivery history.
- Add idempotency protections.
- Add job failure visibility and manual retry.

**Acceptance criteria:** Temporary failures are recoverable, repeated tasks are safe, and webhook failures do not corrupt document state.

### Phase 8: Production Hardening

- Complete unit and integration tests.
- Add end-to-end scenarios.
- Implement evaluation metrics.
- Harden file and API security.
- Improve dashboard metrics.
- Document local setup and deployment.
- Run the full test suite.

**Acceptance criteria:** The project can be installed from the documentation, its main workflow works end to end, and critical failure paths are tested.

---

## 24. Definition of Done

The project is not complete merely because the dashboard looks polished.

The MVP is complete when:

- [ ] A user can authenticate and upload a supported document.
- [ ] The document is stored and assigned a stable ID.
- [ ] Processing happens asynchronously.
- [ ] Digital PDFs and scanned images follow appropriate parsing paths.
- [ ] Classification and extraction results are persisted.
- [ ] Schema and semantic validation execute.
- [ ] Confidence assessment is explainable.
- [ ] Business rules execute deterministically.
- [ ] Duplicate submissions are handled safely.
- [ ] Uncertain documents enter the review queue.
- [ ] Reviewers can correct fields and make authorized decisions.
- [ ] Original extraction results and review history are preserved.
- [ ] State transitions are enforced on the server.
- [ ] Audit events are available.
- [ ] Webhooks are signed, retryable, and independently processed.
- [ ] The dashboard displays actual backend data.
- [ ] Authentication and document access controls are tested.
- [ ] The core test suite passes.
- [ ] The evaluation process reports meaningful extraction and decision metrics.
- [ ] Docker Compose starts the documented application stack.
- [ ] README and API documentation reflect the actual implementation.

---

## 25. Instructions to the Coding Agent

Treat this README as the project's primary implementation specification.

### Before Coding

1. Inspect the existing repository, source files, dependencies, and current implementation.
2. Identify which required components already exist.
3. Reuse existing working components instead of duplicating them.
4. Identify missing dependencies and architectural conflicts.
5. Create a short implementation plan with milestones.
6. Record significant architectural decisions when a deviation is necessary.

### During Implementation

1. Build the project incrementally, following the implementation phases.
2. Keep API handlers thin and place business logic in testable services.
3. Use typed Python models, typed API contracts, and database migrations.
4. Use decimal arithmetic for financial amounts.
5. Keep parsing, OCR, classification, extraction, validation, rules, decisions, review, and webhooks as separate responsibilities.
6. Implement the mock extraction provider before requiring a real provider key.
7. Use deterministic fixtures for tests rather than relying on live LLM responses.
8. Never fabricate extraction results, processing metrics, or completed integrations.
9. Implement loading, error, empty, and success states in the frontend.
10. Ensure each major feature has automated tests.
11. Update this README when an implementation decision materially changes the design.
12. Never store real credentials or secrets in the repository.

### Required Engineering Practices

- Use transactions for critical state changes.
- Make background tasks idempotent.
- Use explicit database constraints.
- Validate all external input.
- Enforce authorization server-side.
- Preserve extraction and review history.
- Use structured errors and logs.
- Keep secrets and document contents out of normal logs.
- Document limitations and unimplemented features honestly.
- Avoid overengineering the MVP.

### Final Verification

Before reporting completion:

1. Run database migrations from a clean database.
2. Start the application using the documented setup.
3. Run backend unit and integration tests.
4. Run frontend tests and a production build.
5. Execute the main end-to-end invoice workflow.
6. Test duplicate handling, review, retries, and webhook failures.
7. Verify that the dashboard uses actual API responses.
8. Verify access controls and file protection.
9. Update documentation with tested commands.
10. Report completed features, test results, known limitations, and remaining work.

Do not claim a feature is complete merely because a file, endpoint, component, or placeholder exists.

---

## 26. Expected Final Outcome

The final product should be a working document operations platform rather than a simple AI demo.

It should demonstrate:

- AI-assisted document understanding.
- OCR and structured information extraction.
- Backend API engineering.
- Typed data contracts and database design.
- Asynchronous job processing.
- Deterministic business logic.
- Duplicate detection and anomaly flagging.
- Human-in-the-loop workflows.
- Auditability and security.
- External system integration through webhooks.
- A functional operational dashboard.
- Automated testing and measurable AI evaluation.

The most important architectural principle is this:

**AI extracts and interprets information; deterministic code validates it; explicit policies determine the outcome; authorized humans handle uncertainty and exceptions; the audit trail records what happened.**

That separation is what turns document extraction into a useful business system.
