import structlog

from celery import shared_task

from dashboard.services.energinet import fetch_latest_spot_prices

logger = structlog.get_logger()


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


@shared_task(ignore_result=True)
def broadcast_current_price() -> None:
    """
    Broadcast the current electricity price to all WebSocket clients.
    Called by Celery beat every 15 minutes at :00, :15, :30, :45.
    """
    import asyncio
    from channels.layers import get_channel_layer
    from django.utils import timezone
    from dashboard.services.current_price import get_current_price

    channel_layer = get_channel_layer()
    now = timezone.now()

    for area in ("DK1", "DK2"):
        ctx = get_current_price(now, area)
        if ctx is None:
            continue

        message = {
            "type": "price.update",
            "area": area,
            "price": str(ctx.current_price),
            "spot": str(ctx.spot_price),
            "trend_direction": ctx.trend_direction,
            "trend_pct": str(ctx.trend_pct) if ctx.trend_pct is not None else None,
            "color": ctx.color,
        }

        asyncio.run(channel_layer.group_send("price_ticker", message))
        logger.info("price_broadcast", area=area, price=str(ctx.current_price))
