import re

import structlog

logger = structlog.get_logger()

EXCLUDE_PATHS = re.compile(
    r"^/(static|media|admin|health|api/health|favicon\.ico|robots\.txt|sitemap\.xml|api/visitors)"
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

        # Nginx sets this from its direct peer address. Do not trust a client-supplied
        # X-Forwarded-For header, which would make visitor analytics spoofable.
        ip = request.META.get("HTTP_X_REAL_IP", "") or request.META.get("REMOTE_ADDR", "")

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
            logger.warning("visitor_tracking_queue_failed")

        return response
