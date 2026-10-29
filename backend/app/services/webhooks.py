import json
import uuid
import secrets
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import sign_webhook_payload
from backend.app.db.models.models import WebhookEndpoint, WebhookDelivery
from backend.app.core.logging import logger


class WebhookService:
    @staticmethod
    def register_endpoint(
        db: Session,
        name: str,
        url: str,
        subscribed_events: List[str],
        enabled: bool = True,
    ) -> Tuple[WebhookEndpoint, str]:
        """
        Register a new webhook endpoint. Returns (endpoint, cleartext_secret).
        The cleartext secret is returned only once at creation.
        """
        secret = secrets.token_hex(32)
        endpoint = WebhookEndpoint(
            id=str(uuid.uuid4()),
            name=name,
            url=url,
            secret_reference=secret,
            subscribed_events=subscribed_events,
            enabled=enabled,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)
        return endpoint, secret

    @classmethod
    def dispatch_event(
        cls,
        db: Session,
        event_type: str,
        document_id: str,
        payload_data: Dict[str, Any],
    ) -> List[str]:
        """
        Find subscribed webhook endpoints and enqueue or dispatch deliveries.
        """
        endpoints = db.query(WebhookEndpoint).filter(WebhookEndpoint.enabled == True).all()
        delivery_ids = []

        for ep in endpoints:
            subscribed = ep.subscribed_events or []
            if event_type in subscribed or "*" in subscribed:
                event_id = str(uuid.uuid4())
                payload = {
                    "event_id": event_id,
                    "event_type": event_type,
                    "document_id": document_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": payload_data,
                }

                delivery = WebhookDelivery(
                    id=str(uuid.uuid4()),
                    endpoint_id=ep.id,
                    event_id=event_id,
                    event_type=event_type,
                    payload=payload,
                    status="pending",
                    attempt_count=0,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(delivery)
                db.commit()
                db.refresh(delivery)
                delivery_ids.append(delivery.id)

                # Attempt immediate delivery
                cls.deliver_webhook(db, delivery.id)

        return delivery_ids

    @classmethod
    def deliver_webhook(cls, db: Session, delivery_id: str) -> bool:
        delivery = db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return False

        endpoint = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == delivery.endpoint_id).first()
        if not endpoint:
            delivery.status = "failed"
            delivery.last_error = "Endpoint no longer exists"
            db.commit()
            return False

        payload_bytes = json.dumps(delivery.payload, sort_keys=True).encode("utf-8")
        signature = sign_webhook_payload(payload_bytes, endpoint.secret_reference)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery-Id": delivery.id,
        }

        delivery.attempt_count += 1

        try:
            with httpx.Client(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
                resp = client.post(endpoint.url, content=payload_bytes, headers=headers)
                delivery.last_http_status = resp.status_code

                if 200 <= resp.status_code < 300:
                    delivery.status = "delivered"
                    delivery.delivered_at = datetime.now(timezone.utc)
                    delivery.last_error = None
                    db.commit()
                    logger.info(f"Webhook delivery '{delivery.id}' to '{endpoint.url}' succeeded.")
                    return True
                else:
                    delivery.last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            delivery.last_error = str(e)[:300]
            logger.warning(f"Webhook delivery '{delivery.id}' to '{endpoint.url}' failed: {e}")

        # Check retry policy (up to 3 attempts with exponential backoff)
        if delivery.attempt_count < 3:
            delivery.status = "retrying"
            backoff_seconds = [5, 30, 120][delivery.attempt_count - 1]
            delivery.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
        else:
            delivery.status = "failed"

        db.commit()
        return False
