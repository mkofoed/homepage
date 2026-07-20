"""Celery tasks used by the public engineering demonstrations."""

from time import sleep

from celery import shared_task

from .services.request_lifecycle import publish_progress


@shared_task(bind=True, ignore_result=True, soft_time_limit=10, time_limit=15)
def complete_request_lifecycle(self, correlation_id: str) -> None:
    """Complete a short, isolated Celery task and stream its lifecycle events."""
    task_id = self.request.id or "unknown"
    publish_progress(
        correlation_id,
        stage="celery",
        status="running",
        detail=f"Worker accepted task {task_id[:8]}.",
    )

    # This bounded delay makes queue hand-off visible without processing visitor data.
    sleep(0.35)

    publish_progress(
        correlation_id,
        stage="celery",
        status="complete",
        detail="Isolated task completed; no visitor data was stored.",
    )
