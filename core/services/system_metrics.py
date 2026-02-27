import logging
import time

import psutil
from django.db import connection

logger = logging.getLogger(__name__)


def check_database_health() -> tuple[bool, float]:
    """Check database connectivity and response time.

    Returns:
        Tuple of (is_healthy, response_time_ms)
    """
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

    return db_healthy, db_response_ms


def get_system_metrics() -> dict:
    """Get system metrics including CPU and memory usage.

    Returns:
        Dictionary containing system metrics.
    """
    cpu_percent: float = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    return {
        "cpu_percent": cpu_percent,
        "memory_percent": round(memory.percent, 1),
        "memory_used_mb": round(memory.used / (1024 * 1024), 1),
        "memory_total_mb": round(memory.total / (1024 * 1024), 1),
    }
