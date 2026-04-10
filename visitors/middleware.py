import hashlib
import datetime
import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

EXCLUDE_PATHS = re.compile(
    r"^/(static|media|admin|health|api/health|favicon\\.ico|robots\\.txt|sitemap\\.xml|api/visitors)"
)

BOT_PATTERN = re.compile(
    r"(bot|crawl|spider|slurp|baidu|yandex|duckduck|semrush|ahref|mj12)",
    re.IGNORECASE,
)

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not (200 <= response.status_code < 300):
            return response

        path = request.path

        if EXCLUDE_PATHS.match(path):
            return response

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        if BOT_PATTERN.search(user_agent):
            return response

        if getattr(request, "htmx", False):
            return response

        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        if not ip:
            ip = request.META.get("REMOTE_ADDR", "")

        if not ip:
            return response

        from visitors.tasks import log_page_view

        device_type = "desktop"
        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower:
            device_type = "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            device_type = "tablet"

        try:
            log_page_view.delay(ip=ip, path=path, device_type=device_type)
        except Exception:
            logger.warning("Failed to queue page view tracking task", exc_info=True)

        return response