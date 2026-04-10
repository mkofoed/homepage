import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


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

    location = lookup_ip(ip)
    if location is None:
        return

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
        raise self.retry(exc=exc)
