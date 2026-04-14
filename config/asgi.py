"""
ASGI config — routes HTTP through Django and WebSockets through Channels.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Must be called before importing channels or any models
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402
from django.conf import settings  # noqa: E402
import config.ws_routing as ws_routing  # noqa: E402

ws_stack = AuthMiddlewareStack(URLRouter(ws_routing.websocket_urlpatterns))

# Only enforce origin validation in production
if not settings.DEBUG:
    ws_stack = AllowedHostsOriginValidator(ws_stack)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": ws_stack,
    }
)
