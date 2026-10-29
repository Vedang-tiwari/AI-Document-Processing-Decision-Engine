from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "document_engine",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Autodiscover tasks
celery_app.autodiscover_tasks(["backend.app.tasks"])
