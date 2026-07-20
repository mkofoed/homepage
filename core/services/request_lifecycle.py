"""Services supporting the public request-lifecycle demonstration."""

from dataclasses import dataclass
from hashlib import sha256
from time import perf_counter

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache


@dataclass(frozen=True)
class CacheProbe:
    """The safe, non-persistent cache measurement shown in the demo."""

    hit: bool
    duration_ms: float


def get_lifecycle_group(correlation_id: str) -> str:
    """Return the Channels group dedicated to a single client-generated trace."""
    return f"request_lifecycle_{correlation_id}"


def probe_cache() -> CacheProbe:
    """Perform a bounded cache read/write without storing visitor data."""
    started_at = perf_counter()
    cache_key = "request_lifecycle:probe:v1"
    hit = cache.get(cache_key) is not None

    if not hit:
        cache.set(cache_key, {"purpose": "homepage-demo"}, timeout=60)

    return CacheProbe(hit=hit, duration_ms=round((perf_counter() - started_at) * 1000, 2))


def get_rate_limit_key(client_address: str) -> str:
    """Return a cache key without retaining a raw client IP address."""
    address_hash = sha256(client_address.encode()).hexdigest()
    return f"request_lifecycle:rate_limit:{address_hash}"


def publish_progress(correlation_id: str, stage: str, status: str, detail: str) -> None:
    """Publish a lifecycle update to the WebSocket waiting for this trace."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        raise RuntimeError("The request lifecycle demo requires a configured channel layer.")

    async_to_sync(channel_layer.group_send)(
        get_lifecycle_group(correlation_id),
        {
            "type": "lifecycle.progress",
            "stage": stage,
            "status": status,
            "detail": detail,
        },
    )
