from backend.app.tasks.celery_app import celery_app
from backend.app.db.session import SessionLocal
from backend.app.services.webhooks import WebhookService


@celery_app.task(name="backend.app.tasks.webhook_tasks.deliver_webhook_task")
def deliver_webhook_task(delivery_id: str):
    db = SessionLocal()
    try:
        WebhookService.deliver_webhook(db, delivery_id)
    finally:
        db.close()
