import json
import time
from uuid import UUID

import structlog
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

logger = structlog.get_logger()


@ensure_csrf_cookie
def home(request: HttpRequest) -> HttpResponse:
    """Home page view with featured cards."""
    from blog.models import Post

    from .services.github_service import get_github_stats

    latest_posts = Post.objects.filter(status=Post.Status.PUBLISHED).order_by("-created_at")[:3]
    github = get_github_stats()

    return render(
        request,
        "core/home.html",
        {
            "latest_posts": latest_posts,
            "github": github,
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    """About page view."""
    return render(request, "core/about.html")


def architecture(request: HttpRequest) -> HttpResponse:
    """Architecture page showing how the site is built."""
    return render(request, "core/architecture.html")


def visitor_map(request: HttpRequest) -> HttpResponse:
    """Visitor map showcase page."""
    from django.db import ProgrammingError
    from django.db.models import Count

    from visitors.models import PageView

    try:
        total_views = PageView.objects.count()
        unique_visitors = PageView.objects.values("ip_hash").distinct().count()
        top_countries = list(
            PageView.objects.values("country_name", "country_code")
            .annotate(count=Count("ip_hash", distinct=True))
            .order_by("-count")[:10]
        )
        device_counts = list(
            PageView.objects.values("device_type").annotate(count=Count("ip_hash", distinct=True)).order_by("-count")
        )
        unique_countries = PageView.objects.values("country_code").distinct().count()
    except ProgrammingError:
        total_views = 0
        unique_visitors = 0
        top_countries = []
        device_counts = []
        unique_countries = 0

    return render(
        request,
        "core/visitor_map.html",
        {
            "total_views": total_views,
            "unique_visitors": unique_visitors,
            "top_countries": top_countries,
            "device_counts": device_counts,
            "unique_countries": unique_countries,
        },
    )


def visitor_map_data(request: HttpRequest) -> JsonResponse:
    """API endpoint returning k-anonymous, approximate visitor geo data for the map."""
    from django.db import ProgrammingError
    from django.db.models import Count
    from django.db.models.functions import Round

    from visitors.models import PageView

    try:
        # Group visitors into approximately 11 km cells and suppress cells with fewer
        # than three visitors so the public map cannot identify an individual.
        points = (
            PageView.objects.annotate(
                latitude_cell=Round("latitude", precision=1), longitude_cell=Round("longitude", precision=1)
            )
            .values("latitude_cell", "longitude_cell", "country_name", "country_code")
            .annotate(visitors=Count("ip_hash", distinct=True))
            .filter(visitors__gte=3)
            .order_by("-visitors")
        )
        features = []
        for p in points:
            if p["latitude_cell"] is not None and p["longitude_cell"] is not None:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [p["longitude_cell"], p["latitude_cell"]],
                        },
                        "properties": {
                            "country": p["country_name"],
                            "country_code": p["country_code"],
                            "count": p["visitors"],
                        },
                    }
                )
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
        },
        status=200 if db_healthy else 503,
    )


def github_stats(request: HttpRequest) -> HttpResponse:
    """API endpoint returning GitHub stats as HTML partial."""
    from .services.github_service import get_github_stats

    logger.info("Fetching GitHub stats")
    stats = get_github_stats()

    if stats is None:
        logger.warning("GitHub stats returned None")

    return render(request, "core/partials/github_stats.html", {"stats": stats})


@require_POST
def request_lifecycle(request: HttpRequest) -> JsonResponse:
    """Start a bounded, UUID-scoped request lifecycle demonstration."""
    from .services.request_lifecycle import get_rate_limit_key, probe_cache, publish_progress
    from .tasks import complete_request_lifecycle

    try:
        payload = json.loads(request.body)
        correlation_id = str(UUID(payload["correlation_id"]))
    except json.JSONDecodeError, KeyError, TypeError, ValueError:
        return JsonResponse({"error": "A valid correlation_id UUID is required."}, status=400)

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    client_address = forwarded_for.rsplit(",", maxsplit=1)[-1].strip() or request.META.get("REMOTE_ADDR", "")
    if not cache.add(get_rate_limit_key(client_address), True, timeout=20):
        return JsonResponse({"error": "Please wait a few seconds before running another trace."}, status=429)

    cache_probe = probe_cache()
    cache_detail = (
        f"{'Cache hit' if cache_probe.hit else 'Cache miss'} in {cache_probe.duration_ms:.2f} ms; "
        "the probe contains no visitor data."
    )
    publish_progress(
        correlation_id,
        stage="nginx",
        status="complete",
        detail=(
            "Nginx reverse proxy forwarded the request."
            if forwarded_for
            else "Local development request connected directly."
        ),
    )
    publish_progress(
        correlation_id,
        stage="django",
        status="complete",
        detail="Django validated the supplied correlation ID.",
    )
    publish_progress(correlation_id, stage="redis", status="complete", detail=cache_detail)
    publish_progress(
        correlation_id,
        stage="celery",
        status="queued",
        detail="Dispatching an isolated task to a Celery worker.",
    )

    try:
        task = complete_request_lifecycle.delay(correlation_id)
    except Exception:
        logger.exception("request_lifecycle_task_dispatch_failed", correlation_id=correlation_id)
        publish_progress(
            correlation_id,
            stage="celery",
            status="error",
            detail="The task queue is temporarily unavailable.",
        )
        return JsonResponse({"error": "The task queue is temporarily unavailable."}, status=503)

    logger.info("request_lifecycle_started", correlation_id=correlation_id, cache_hit=cache_probe.hit)

    return JsonResponse(
        {
            "correlation_id": correlation_id,
            "cache": {"hit": cache_probe.hit, "duration_ms": cache_probe.duration_ms},
            "task_id": task.id,
        },
        status=202,
    )


def public_metrics(request: HttpRequest) -> JsonResponse:
    """Public API endpoint returning lightweight server stats for the architecture page."""
    import sys

    import django
    from django.db import connection

    from .services.system_metrics import check_database_health, get_system_metrics

    metrics_data = get_system_metrics()
    _, db_response_ms = check_database_health()

    # Hypertable row counts via TimescaleDB approximate count (fast)
    # Cached in Redis for 60s — numbers change slowly (hourly ingest)
    from django.core.cache import cache

    hypertable_stats = cache.get("hypertable_stats")
    if hypertable_stats is None:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        hypertable_name,
                        approximate_row_count(format('%I.%I', hypertable_schema, hypertable_name)::regclass) AS row_count
                    FROM timescaledb_information.hypertables
                    ORDER BY hypertable_name;
                """)
                hypertable_stats = [{"table": row[0], "rows": row[1]} for row in cursor.fetchall()]
                cache.set("hypertable_stats", hypertable_stats, timeout=60)
        except Exception:
            hypertable_stats = []

    return JsonResponse(
        {
            "cpu_percent": metrics_data["cpu_percent"],
            "memory_percent": metrics_data["memory_percent"],
            "db_response_ms": db_response_ms,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "django_version": django.__version__,
            "hypertables": hypertable_stats,
        }
    )


def api_playground(request: HttpRequest) -> HttpResponse:
    """Interactive API playground showcase page."""
    return render(request, "core/api_playground.html")


@login_required
def metrics(request: HttpRequest) -> JsonResponse:
    """API endpoint returning server metrics."""
    from .services.system_metrics import check_database_health, get_system_metrics

    metrics_data = get_system_metrics()
    _, db_response_ms = check_database_health()
    metrics_data["db_response_ms"] = db_response_ms

    return JsonResponse(metrics_data)
