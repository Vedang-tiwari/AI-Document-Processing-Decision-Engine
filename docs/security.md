# Security & Data Privacy

## Threat Model and Safeguards

1. **Untrusted Document Ingestion**:
   - Magic byte signature validation on all uploaded files.
   - Max file size limits strictly enforced (20 MB default).
   - Storage keys are randomized UUIDs preventing path traversal and name collisions.
   - Access to original documents is guarded by authenticated endpoints (`/api/v1/documents/{id}/file`).

2. **Prompt Injection & Model Untrustworthiness**:
   - Text extracted from documents is treated strictly as data.
   - Extraction output is parsed through strict Pydantic models.
   - Financial decisions are computed solely by deterministic Python code, never by the LLM.

3. **Data Protection & Auditability**:
   - Secrets, full prompts, passwords, and sensitive PII are excluded from ordinary logs.
   - Webhook signing secrets are hashed / stored securely and never returned in collection APIs.
   - Review records and audit events are immutable.

4. **Webhook Security**:
   - Webhook payloads are signed using HMAC-SHA256 (`X-Webhook-Signature`).
   - Server-Side Request Forgery (SSRF) protections.
