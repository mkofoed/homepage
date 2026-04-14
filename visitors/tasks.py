import structlog

from celery import shared_task
from django.utils import timezone

logger = structlog.get_logger()

# How long to cache visitor location (24h — rotates with daily IP hash)
LOCATION_CACHE_TTL = 86400


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=10,
    time_limit=15,
    ignore_result=True,
)
def log_page_view(self, *, ip: str, path: str, device_type: str = "desktop") -> None:
    from visitors.models import PageView
    from visitors.services.geoip import lookup_ip
    from django.core.cache import cache

    location = lookup_ip(ip)
    if location is None:
        return

    # Cache location by ip_hash so WebSocket consumers can read it quickly
    cache.set(
        f"visitor_location_{location.ip_hash}",
        {
            "lat": location.latitude,
            "lon": location.longitude,
            "city": location.city,
            "country": location.country_name,
        },
        timeout=LOCATION_CACHE_TTL,
    )

    try:
        PageView.objects.create(
            timestamp=timezone.now(),
            ip_hash=location.ip_hash,
            country_code=location.country_code,
            country_name=location.country_name,
            city=location.city,
            latitude=location.latitude,
            longitude=location.longitude,
            path=path,
            device_type=device_type,
        )
    except Exception as exc:
        logger.warning("Failed to create PageView", exc_info=True)
        raise self.retry(exc=exc) from exc
