from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class WebhookCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    url: str = Field(..., min_length=8, max_length=2048)
    subscribed_events: List[str] = Field(
        default=[
            "document.processing_completed",
            "document.review_required",
            "document.processing_failed",
            "document.review_completed",
        ]
    )
    enabled: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    subscribed_events: Optional[List[str]] = None
    enabled: Optional[bool] = None


class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    subscribed_events: List[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    # Note: secret_reference is never returned in cleartext to comply with README section 8.9 & 13.6

    class Config:
        from_attributes = True


class WebhookDeliveryItem(BaseModel):
    id: str
    endpoint_id: str
    event_id: str
    event_type: str
    status: str
    attempt_count: int
    last_http_status: Optional[int] = None
    last_error: Optional[str] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None
    payload: Dict[str, Any] = {}

    class Config:
        from_attributes = True
