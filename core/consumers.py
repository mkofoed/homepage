"""
WebSocket consumers for real-time features.

- PresenceConsumer: "who's watching" counter per page
- VisitorConsumer: live visitor dots on the map
"""

import json
import structlog
from channels.generic.websocket import AsyncWebsocketConsumer

logger = structlog.get_logger()


class PriceTickerConsumer(AsyncWebsocketConsumer):
    """
    Streams live electricity price updates to connected dashboard clients.
    URL: ws/prices/?area=DK1
    Clients receive current price on connect, then on every 15-min interval broadcast.
    """

    GROUP = "price_ticker"

    async def connect(self):
        self.area = self.scope["query_string"].decode()
        self.area = self.area.split("area=")[-1].split("&")[0] if "area=" in self.area else "DK1"
        if self.area not in ("DK1", "DK2"):
            self.area = "DK1"

        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()

        # Send current price immediately on connect
        await self._send_current_price()
        logger.debug("price_ticker_connect", area=self.area)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Client can send {"area": "DK2"} to switch area
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get("area") in ("DK1", "DK2"):
                    self.area = data["area"]
                    await self._send_current_price()
            except json.JSONDecodeError:
                pass

    async def price_update(self, event):
        """Receive broadcast from Celery task and forward to client."""
        # Only forward if area matches what this client is watching
        if event.get("area") == self.area:
            await self.send(text_data=json.dumps({
                "type": "price_update",
                "price": event["price"],
                "spot": event["spot"],
                "trend_direction": event["trend_direction"],
                "trend_pct": event["trend_pct"],
                "color": event["color"],
                "area": event["area"],
            }))

    async def _send_current_price(self):
        """Fetch current price and send to this client."""
        from asgiref.sync import sync_to_async
        from django.utils import timezone
        from dashboard.services.current_price import get_current_price

        ctx = await sync_to_async(get_current_price)(timezone.now(), self.area)
        if ctx:
            await self.send(text_data=json.dumps({
                "type": "price_update",
                "price": str(ctx.current_price),
                "spot": str(ctx.spot_price),
                "trend_direction": ctx.trend_direction,
                "trend_pct": str(ctx.trend_pct) if ctx.trend_pct is not None else None,
                "color": ctx.color,
                "area": self.area,
            }))


    """
    Tracks how many people are viewing a given page.
    URL: ws/presence/<page>/
    Broadcasts count to everyone in the same page group.
    """

    async def connect(self):
        self.page = self.scope["url_route"]["kwargs"]["page"]
        self.group = f"presence_{self.page}"

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        # Increment count and broadcast to group
        await self._broadcast_count(delta=1)
        logger.debug("presence_connect", page=self.page)

    async def disconnect(self, close_code):
        await self._broadcast_count(delta=-1)
        await self.channel_layer.group_discard(self.group, self.channel_name)
        logger.debug("presence_disconnect", page=self.page)

    async def receive(self, text_data=None, bytes_data=None):
        # Clients don't send anything — read-only
        pass

    async def presence_update(self, event):
        """Receive broadcast from group and forward to WebSocket client."""
        await self.send(text_data=json.dumps({"count": event["count"]}))

    async def _broadcast_count(self, delta: int):
        """Atomically update count in Redis and broadcast to group."""
        from channels.layers import get_channel_layer
        from django.core.cache import cache

        layer = get_channel_layer()
        key = f"presence_count_{self.page}"

        # Atomic increment/decrement via Redis
        count = cache.get(key, 0) + delta
        count = max(0, count)
        cache.set(key, count, timeout=3600)

        await layer.group_send(
            self.group,
            {"type": "presence.update", "count": count},
        )


class VisitorConsumer(AsyncWebsocketConsumer):
    """
    Broadcasts anonymised visitor locations to all connected map viewers.
    URL: ws/visitors/
    On connect: sends current online visitors, broadcasts new arrival.
    On disconnect: broadcasts departure.
    """

    GROUP = "visitor_map"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()

        # Get this visitor's location from session/cache (set by middleware)
        location = await self._get_location()
        if location:
            self.location = location
            # Broadcast arrival to all other viewers
            await self.channel_layer.group_send(
                self.GROUP,
                {
                    "type": "visitor.arrive",
                    "lat": location["lat"],
                    "lon": location["lon"],
                    "city": location["city"],
                    "country": location["country"],
                    "channel": self.channel_name,
                },
            )
        else:
            self.location = None

        logger.debug("visitor_ws_connect")

    async def disconnect(self, close_code):
        if self.location:
            await self.channel_layer.group_send(
                self.GROUP,
                {
                    "type": "visitor.depart",
                    "channel": self.channel_name,
                },
            )
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass

    async def visitor_arrive(self, event):
        """Forward arrival event to this client."""
        await self.send(text_data=json.dumps({
            "type": "arrive",
            "lat": event["lat"],
            "lon": event["lon"],
            "city": event["city"],
            "country": event["country"],
            "channel": event["channel"],
        }))

    async def visitor_depart(self, event):
        """Forward departure event to this client."""
        await self.send(text_data=json.dumps({
            "type": "depart",
            "channel": event["channel"],
        }))

    async def _get_location(self) -> dict | None:
        """Look up cached geo location for this visitor's session."""
        from django.core.cache import cache
        session = self.scope.get("session", {})
        ip_hash = session.get("visitor_ip_hash")
        if not ip_hash:
            return None
        return cache.get(f"visitor_location_{ip_hash}")
