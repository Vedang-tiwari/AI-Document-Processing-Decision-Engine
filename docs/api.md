# REST API Reference

Base URL prefix: `/api/v1`

## Authentication

All protected endpoints expect a Bearer JWT token in the `Authorization` header:
```http
Authorization: Bearer <jwt-token>
```

In development mode (`APP_ENV=development`), requests without an Authorization header default to an operator/admin context for rapid local testing.

## Standard Error Format

All error responses strictly follow the standard format:
```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document does not exist.",
    "request_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "details": {}
  }
}
```

## Endpoints Summary

### Documents
- `POST /api/v1/documents`: Upload file (`multipart/form-data`) -> `202 Accepted`
- `GET /api/v1/documents`: List documents with filters (`status`, `document_type`, `page`, `page_size`)
- `GET /api/v1/documents/{document_id}`: Get document metadata and status
- `GET /api/v1/documents/{document_id}/results`: Get extracted fields, evidence, and rule outcomes
- `GET /api/v1/documents/{document_id}/file`: Download / stream original uploaded file
- `POST /api/v1/documents/{document_id}/retry`: Retry eligible failed document

### Human Review
- `GET /api/v1/reviews`: List review queue
- `GET /api/v1/reviews/{document_id}`: Full review workspace detail
- `POST /api/v1/reviews/{document_id}/correct`: Submit field corrections and revalidate
- `POST /api/v1/reviews/{document_id}/decision`: Record authorized decision (`approved` or `rejected`)

### Business Rules
- `GET /api/v1/rules`: List configured rules
- `PATCH /api/v1/rules/{rule_code}`: Toggle enabled state or update configuration

### Webhooks
- `POST /api/v1/webhooks`: Register endpoint (returns signing secret)
- `GET /api/v1/webhooks`: List endpoints
- `PATCH /api/v1/webhooks/{webhook_id}`: Update endpoint
- `DELETE /api/v1/webhooks/{webhook_id}`: Remove endpoint
- `GET /api/v1/webhooks/{webhook_id}/deliveries`: Delivery logs
- `POST /api/v1/webhooks/{webhook_id}/deliveries/{delivery_id}/retry`: Trigger manual retry

### Dashboard
- `GET /api/v1/dashboard/summary`: Status counts
- `GET /api/v1/dashboard/processing-metrics`: Median durations, success rates, confidence
- `GET /api/v1/dashboard/recent-errors`: Recent failures
