from celery import Celery
from app.config import settings
import os

# Create directories for filesystem broker
if settings.CELERY_BROKER_URL == "filesystem://":
    os.makedirs("./celery_data/out", exist_ok=True)
    os.makedirs("./celery_data/processed", exist_ok=True)
    os.makedirs("./celery_results", exist_ok=True)

celery_app = Celery(
    "order_management",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.order_tasks",
        "app.tasks.return_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.invoice_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Add broker transport options if using filesystem
if settings.CELERY_BROKER_URL == "filesystem://":
    celery_app.conf.broker_transport_options = settings.CELERY_BROKER_TRANSPORT_OPTIONS

