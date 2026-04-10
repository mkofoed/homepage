import logging

from celery import shared_task

from dashboard.services.energinet import fetch_latest_spot_prices

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300, soft_time_limit=120, time_limit=180)
def poll_energinet_prices_task(self, limit: int = 24) -> int:
    """
    Celery task to fetch the latest electricity prices and save them to the DB.
    """
    try:
        logger.info("Starting Celery task to poll latest %d spot prices...", limit)
        inserted_dk1 = fetch_latest_spot_prices(limit=limit, price_area="DK1")
        inserted_dk2 = fetch_latest_spot_prices(limit=limit, price_area="DK2")
        inserted = inserted_dk1 + inserted_dk2
        logger.info("Celery task complete. Inserted %d spot price records.", inserted)
        return inserted
    except Exception as exc:
        logger.exception("Failed to poll Energinet prices")
        raise self.retry(exc=exc) from exc
