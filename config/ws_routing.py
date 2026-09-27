"""WebSocket URL routing — all ws:// paths registered here."""

from django.urls import re_path

from core import consumers

websocket_urlpatterns = [
    re_path(r"^ws/presence/(?P<page>[A-Za-z0-9_-]{1,50})/$", consumers.PresenceConsumer.as_asgi()),
    re_path(r"^ws/prices/$", consumers.PriceTickerConsumer.as_asgi()),
    re_path(
        r"^ws/request-lifecycle/(?P<correlation_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$",
        consumers.RequestLifecycleConsumer.as_asgi(),
    ),
]
