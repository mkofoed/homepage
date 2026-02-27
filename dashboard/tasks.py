from celery import shared_task
import logging

from dashboard.services.energinet import fetch_latest_spot_prices

logger = logging.getLogger(__name__)


@shared_task
def poll_energinet_prices_task(limit: int = 24):
    """
    Celery task to fetch the latest electricity prices and save them to the DB.
    """
    logger.info(f"Starting Celery task to poll latest {limit} spot prices...")
    inserted = fetch_latest_spot_prices(limit=limit)
    logger.info(f"Celery task complete. Inserted {inserted} spot price records.")
    return inserted
