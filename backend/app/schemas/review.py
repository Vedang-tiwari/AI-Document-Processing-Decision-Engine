from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCorrectionRequest(BaseModel):
    corrections: Dict[str, Any] = Field(..., description="Map of field paths to corrected values")
    comment: Optional[str] = Field(None, description="Explanation for the manual correction")


class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., description="Decision choice: 'approved' or 'rejected'")
    comment: Optional[str] = Field(None, description="Reviewer notes or reason")


class ReviewQueueItem(BaseModel):
    document_id: str
    original_filename: str
    mime_type: str
    document_type: str
    status: str
    created_at: datetime
    confidence_score: Optional[float] = None
    validation_issue_count: int = 0
    supplier_name: Optional[str] = None
    total_amount: Optional[str] = None


class ReviewQueueResponse(BaseModel):
    items: List[ReviewQueueItem]
    total: int
    page: int
    page_size: int


class ReviewRevisionRecord(BaseModel):
    id: str
    reviewer_id: Optional[str] = None
    action: str
    corrected_data: Dict[str, Any]
    comment: Optional[str] = None
    created_at: datetime


class ReviewDetailResponse(BaseModel):
    document_id: str
    original_filename: str
    mime_type: str
    document_type: str
    status: str
    extracted_data: Optional[Dict[str, Any]] = None
    field_evidence: Optional[Dict[str, Any]] = None
    confidence_data: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    rule_evaluations: List[Dict[str, Any]] = []
    revisions: List[ReviewRevisionRecord] = []
    created_at: datetime
