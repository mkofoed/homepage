import logging
import time

from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    """Home page view."""
    return render(request, 'core/home.html')


def about(request: HttpRequest) -> HttpResponse:
    """About page view."""
    return render(request, 'core/about.html')


def architecture(request: HttpRequest) -> HttpResponse:
    """Architecture page showing how the site is built."""
    return render(request, 'core/architecture.html')


def health_check(request: HttpRequest) -> JsonResponse:
    """API endpoint returning system health metrics."""
    start_time = time.time()
    
    # Check database connectivity
    db_healthy: bool = True
    db_response_ms: float = 0
    try:
        db_start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_response_ms = round((time.time() - db_start) * 1000, 2)
    except Exception as e:
        db_healthy = False
        logger.error("Database health check failed: %s", e)
    
    status = 'healthy' if db_healthy else 'unhealthy'
    if not db_healthy:
        logger.warning("Health check returning unhealthy status")
    
    return JsonResponse({
        'status': status,
        'database': {
            'connected': db_healthy,
            'response_ms': db_response_ms,
        },
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
    })


def github_stats(request: HttpRequest) -> HttpResponse:
    """API endpoint returning GitHub stats as HTML partial."""
    from .services.github_service import get_github_stats
    
    logger.info("Fetching GitHub stats")
    stats = get_github_stats()
    
    if stats is None:
        logger.warning("GitHub stats returned None")
    
    return render(request, 'core/partials/github_stats.html', {'stats': stats})


def dashboard(request: HttpRequest) -> HttpResponse:
    """Real-time metrics dashboard."""
    return render(request, 'core/dashboard.html')


def metrics(request: HttpRequest) -> JsonResponse:
    """API endpoint returning server metrics."""
    import psutil
    
    # Get CPU and memory usage
    cpu_percent: float = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    # Database response time
    db_response_ms: float = 0
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_response_ms = round((time.time() - start) * 1000, 2)
    except Exception as e:
        logger.error("Metrics DB check failed: %s", e)
    
    return JsonResponse({
        'cpu_percent': cpu_percent,
        'memory_percent': round(memory.percent, 1),
        'memory_used_mb': round(memory.used / (1024 * 1024), 1),
        'memory_total_mb': round(memory.total / (1024 * 1024), 1),
        'db_response_ms': db_response_ms,
    })
