"""Cached, privacy-preserving aggregates for the public visitor map.

`page_views` grows with every tracked request, so these full-table aggregations are
cached briefly instead of re-running on each page load or map fetch.
"""

from typing import Any

from django.core.cache import cache
from django.db import ProgrammingError
from django.db.models import Count
from django.db.models.functions import Round

from visitors.models import PageView

CACHE_TIMEOUT = 300  # 5 minutes: tracking is asynchronous and the map is approximate anyway
SUMMARY_CACHE_KEY = "visitors:summary:v1"
MAP_FEATURES_CACHE_KEY = "visitors:map_features:v1"
# Cells with fewer distinct visitors are suppressed so no individual can be singled out.
MIN_VISITORS_PER_CELL = 3


def get_visitor_summary() -> dict[str, Any]:
    """Return headline counts, top countries, and device split for the visitor page."""
    summary = cache.get(SUMMARY_CACHE_KEY)
    if summary is not None:
        return dict(summary)

    try:
        summary = {
            "total_views": PageView.objects.count(),
            "unique_visitors": PageView.objects.values("ip_hash").distinct().count(),
            "top_countries": list(
                PageView.objects.values("country_name", "country_code")
                .annotate(count=Count("ip_hash", distinct=True))
                .order_by("-count")[:10]
            ),
            "device_counts": list(
                PageView.objects.values("device_type")
                .annotate(count=Count("ip_hash", distinct=True))
                .order_by("-count")
            ),
            "unique_countries": PageView.objects.values("country_code").distinct().count(),
        }
    except ProgrammingError:
        # The table is absent before the first migration; do not cache that state.
        return {
            "total_views": 0,
            "unique_visitors": 0,
            "top_countries": [],
            "device_counts": [],
            "unique_countries": 0,
        }

    cache.set(SUMMARY_CACHE_KEY, summary, CACHE_TIMEOUT)
    return summary


def get_visitor_map_features() -> list[dict[str, Any]]:
    """Return k-anonymous GeoJSON features grouped into ~11 km cells."""
    features = cache.get(MAP_FEATURES_CACHE_KEY)
    if features is not None:
        return list(features)

    try:
        points = (
            PageView.objects.annotate(
                latitude_cell=Round("latitude", precision=1), longitude_cell=Round("longitude", precision=1)
            )
            .values("latitude_cell", "longitude_cell", "country_name", "country_code")
            .annotate(visitors=Count("ip_hash", distinct=True))
            .filter(visitors__gte=MIN_VISITORS_PER_CELL)
            .order_by("-visitors")
        )
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p["longitude_cell"], p["latitude_cell"]]},
                "properties": {
                    "country": p["country_name"],
                    "country_code": p["country_code"],
                    "count": p["visitors"],
                },
            }
            for p in points
            if p["latitude_cell"] is not None and p["longitude_cell"] is not None
        ]
    except ProgrammingError:
        return []

    cache.set(MAP_FEATURES_CACHE_KEY, features, CACHE_TIMEOUT)
    return features
