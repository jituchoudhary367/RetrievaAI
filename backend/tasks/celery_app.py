"""
tasks/celery_app.py

Celery application factory.

Uses the same Redis instance already used for pub/sub, on database 1
(pub/sub uses the default db 0) to avoid conflicts.
"""

from __future__ import annotations

from celery import Celery

from app.config import get_settings


def create_celery_app() -> Celery:
    cfg = get_settings()
    broker = cfg.connectors.celery_broker_url
    backend = cfg.connectors.celery_result_backend

    app = Celery(
        "rag_connectors",
        broker=broker,
        backend=backend,
        include=["tasks.connector_tasks", "connectors.tasks"],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # Retry failed tasks automatically
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Keep results for 24 hours
        result_expires=86400,
        # Soft time limit per task (30 minutes)
        task_soft_time_limit=1800,
        task_time_limit=3600,
        # Worker prefetch: one task at a time per worker for long-running downloads
        worker_prefetch_multiplier=1,
    )

    return app


celery_app = create_celery_app()

__all__ = ["celery_app"]
