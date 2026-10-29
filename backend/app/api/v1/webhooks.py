from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.models import WebhookEndpoint, WebhookDelivery
from backend.app.core.security import require_role, CurrentUser
from backend.app.core.exceptions import AppException
from backend.app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookDeliveryItem,
)
from backend.app.services.webhooks import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Register a webhook endpoint")
def create_webhook(
    body: WebhookCreate,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    endpoint, secret = WebhookService.register_endpoint(
        db=db,
        name=body.name,
        url=body.url,
        subscribed_events=body.subscribed_events,
        enabled=body.enabled,
    )
    return {
        "id": endpoint.id,
        "name": endpoint.name,
        "url": endpoint.url,
        "subscribed_events": endpoint.subscribed_events,
        "enabled": endpoint.enabled,
        "secret": secret,  # Returned only upon creation
        "message": "Save this secret securely. It will not be shown again.",
    }


@router.get("", response_model=List[WebhookResponse], summary="List registered webhooks")
def list_webhooks(
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return db.query(WebhookEndpoint).order_by(WebhookEndpoint.created_at.desc()).all()


@router.patch("/{webhook_id}", response_model=WebhookResponse, summary="Update webhook endpoint")
def update_webhook(
    webhook_id: str,
    body: WebhookUpdate,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ep = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not ep:
        raise AppException(404, "WEBHOOK_NOT_FOUND", f"Webhook endpoint '{webhook_id}' not found.")

    if body.name is not None:
        ep.name = body.name
    if body.url is not None:
        ep.url = body.url
    if body.subscribed_events is not None:
        ep.subscribed_events = body.subscribed_events
    if body.enabled is not None:
        ep.enabled = body.enabled

    db.commit()
    db.refresh(ep)
    return ep


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete webhook endpoint")
def delete_webhook(
    webhook_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    ep = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == webhook_id).first()
    if not ep:
        raise AppException(404, "WEBHOOK_NOT_FOUND", f"Webhook endpoint '{webhook_id}' not found.")

    db.delete(ep)
    db.commit()
    return None


@router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryItem], summary="Get webhook delivery history")
def list_deliveries(
    webhook_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.endpoint_id == webhook_id)
        .order_by(WebhookDelivery.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry", summary="Retry a specific webhook delivery")
def retry_delivery(
    webhook_id: str,
    delivery_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    delivery = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.id == delivery_id, WebhookDelivery.endpoint_id == webhook_id)
        .first()
    )
    if not delivery:
        raise AppException(404, "DELIVERY_NOT_FOUND", "Delivery record not found.")

    success = WebhookService.deliver_webhook(db, delivery_id)
    return {
        "delivery_id": delivery_id,
        "success": success,
        "status": delivery.status,
        "last_http_status": delivery.last_http_status,
        "last_error": delivery.last_error,
    }
