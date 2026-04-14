"""WebSocket URL routing — all ws:// paths registered here."""

from django.urls import re_path

from core import consumers

websocket_urlpatterns = [
    re_path(r"^ws/presence/(?P<page>[^/]+)/$", consumers.PresenceConsumer.as_asgi()),
    re_path(r"^ws/visitors/$", consumers.VisitorConsumer.as_asgi()),
]
