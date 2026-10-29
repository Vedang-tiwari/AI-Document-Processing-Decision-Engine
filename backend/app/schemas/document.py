from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    message: str


class DocumentListItem(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    document_type: str
    status: str
    decision_outcome: Optional[str] = None
    processing_attempts: int
    uploaded_by: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    confidence_score: Optional[float] = None
    supplier_name: Optional[str] = None
    total_amount: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentListItem]
    total: int
    page: int
    page_size: int


class ProcessingRunSummary(BaseModel):
    id: str
    run_number: int
    pipeline_version: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_hash: str
    document_type: str
    status: str
    decision_outcome: Optional[str] = None
    processing_attempts: int
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    processing_runs: List[ProcessingRunSummary] = []
    latest_extraction: Optional[Dict[str, Any]] = None
    latest_decision: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class RuleEvaluationItem(BaseModel):
    rule_code: str
    rule_version: int
    status: str
    severity: str
    message: str
    details: Dict[str, Any] = {}


class DocumentResultResponse(BaseModel):
    document_id: str
    status: str
    decision_outcome: Optional[str] = None
    document_type: str
    schema_version: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    field_evidence: Optional[Dict[str, Any]] = None
    confidence_data: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    rule_evaluations: List[RuleEvaluationItem] = []
    created_at: datetime


class RetryResponse(BaseModel):
    document_id: str
    status: str
    message: str
