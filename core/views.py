import logging
import time

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    """Home page view with featured cards."""
    from blog.models import Post
    from .services.github_service import get_github_stats

    latest_posts = Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")[:3]
    github = get_github_stats()

    return render(request, "core/home.html", {
        "latest_posts": latest_posts,
        "github": github,
    })


def about(request: HttpRequest) -> HttpResponse:
    """About page view."""
    return render(request, "core/about.html")


def architecture(request: HttpRequest) -> HttpResponse:
    """Architecture page showing how the site is built."""
    return render(request, "core/architecture.html")


def visitor_map(request: HttpRequest) -> HttpResponse:
    """Visitor map showcase page."""
    from visitors.models import PageView
    from django.db.models import Count
    from django.db import ProgrammingError

    try:
        total_views = PageView.objects.count()
        unique_visitors = PageView.objects.values("ip_hash").distinct().count()
        top_countries = list(
            PageView.objects
            .values("country_name", "country_code")
            .annotate(count=Count("ip_hash", distinct=True))
            .order_by("-count")[:10]
        )
        device_counts = list(
            PageView.objects
            .values("device_type")
            .annotate(count=Count("ip_hash", distinct=True))
            .order_by("-count")
        )
        unique_countries = PageView.objects.values("country_code").distinct().count()
    except ProgrammingError:
        total_views = 0
        unique_visitors = 0
        top_countries = []
        device_counts = []
        unique_countries = 0

    return render(request, "core/visitor_map.html", {
        "total_views": total_views,
        "unique_visitors": unique_visitors,
        "top_countries": top_countries,
        "device_counts": device_counts,
        "unique_countries": unique_countries,
    })


def visitor_map_data(request: HttpRequest) -> JsonResponse:
    """API endpoint returning visitor geo data for the map."""
    from visitors.models import PageView
    from django.db.models import Count
    from django.db import ProgrammingError

    try:
        # Deduplicate by ip_hash first, then aggregate locations
        # This gives unique visitors per location, not raw page views
        points = (
            PageView.objects
            .values("latitude", "longitude", "country_name", "country_code", "city")
            .annotate(visitors=Count("ip_hash", distinct=True))
            .order_by("-visitors")
        )
        features = []
        for p in points:
            if p["latitude"] and p["longitude"]:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [p["longitude"], p["latitude"]],
                    },
                    "properties": {
                        "country": p["country_name"],
                        "country_code": p["country_code"],
                        "city": p["city"] or p["country_name"],
                        "count": p["visitors"],
                    },
                })
    except ProgrammingError:
        features = []

    return JsonResponse({"type": "FeatureCollection", "features": features})

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


def public_metrics(request: HttpRequest) -> JsonResponse:
    """Public API endpoint returning lightweight server stats for the architecture page."""
    from .services.system_metrics import check_database_health, get_system_metrics
    import django
    import sys

    metrics_data = get_system_metrics()
    _, db_response_ms = check_database_health()

    return JsonResponse({
        "cpu_percent": metrics_data["cpu_percent"],
        "memory_percent": metrics_data["memory_percent"],
        "db_response_ms": db_response_ms,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "django_version": django.__version__,
    })


def api_playground(request: HttpRequest) -> HttpResponse:
    """Interactive API playground showcase page."""
    return render(request, "core/api_playground.html")



    """API endpoint returning server metrics."""
    from .services.system_metrics import check_database_health, get_system_metrics

    metrics_data = get_system_metrics()
    _, db_response_ms = check_database_health()
    metrics_data["db_response_ms"] = db_response_ms

    return JsonResponse(metrics_data)
