import logging
import time

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    """Home page view."""
    return render(request, "core/home.html")


def about(request: HttpRequest) -> HttpResponse:
    """About page view."""
    return render(request, "core/about.html")


def architecture(request: HttpRequest) -> HttpResponse:
    """Architecture page showing how the site is built."""
    return render(request, "core/architecture.html")


def health_check(request: HttpRequest) -> JsonResponse:
    """API endpoint returning system health metrics."""
    from .services.system_metrics import check_database_health

    start_time = time.time()
    db_healthy, db_response_ms = check_database_health()

    status = "healthy" if db_healthy else "unhealthy"
    if not db_healthy:
        logger.warning("Health check returning unhealthy status")

    return JsonResponse(
        {
            "status": status,
            "database": {
                "connected": db_healthy,
                "response_ms": db_response_ms,
            },
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }
    )


def github_stats(request: HttpRequest) -> HttpResponse:
    """API endpoint returning GitHub stats as HTML partial."""
    from .services.github_service import get_github_stats

    logger.info("Fetching GitHub stats")
    stats = get_github_stats()

    if stats is None:
        logger.warning("GitHub stats returned None")

    return render(request, "core/partials/github_stats.html", {"stats": stats})


def dashboard(request: HttpRequest) -> HttpResponse:
    """Real-time metrics dashboard."""
    return render(request, "core/dashboard.html")


def metrics(request: HttpRequest) -> JsonResponse:
    """API endpoint returning server metrics."""
    from .services.system_metrics import check_database_health, get_system_metrics

    metrics_data = get_system_metrics()
    _, db_response_ms = check_database_health()
    metrics_data["db_response_ms"] = db_response_ms

    return JsonResponse(metrics_data)
