import json
from datetime import timedelta
from unittest.mock import patch

from asgiref.testing import ApplicationCommunicator
from channels.routing import URLRouter
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post
from config.ws_routing import websocket_urlpatterns
from visitors.models import PageView


class HomeViewTests(TestCase):
    @patch("core.services.github_service.get_github_stats", return_value=None)
    def test_home_links_to_posts_by_primary_key(self, mock_github_stats) -> None:
        author = User.objects.create_user("author")
        post = Post.objects.create(
            author=author,
            title="Published post",
            content="Content",
            status=Post.Status.PUBLISHED,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("blog_detail", args=[post.pk]))
        mock_github_stats.assert_called_once()


class HealthCheckTests(TestCase):
    @patch("core.services.system_metrics.check_database_health", return_value=(False, 0.0))
    def test_health_check_returns_service_unavailable_when_database_is_down(self, mock_health_check) -> None:
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "unhealthy")
        mock_health_check.assert_called_once()


class VisitorMapDataTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def test_map_hides_individual_locations_and_rounds_visible_coordinates(self) -> None:
        timestamp = timezone.now()
        for index in range(3):
            PageView.objects.create(
                timestamp=timestamp + timedelta(microseconds=index),
                ip_hash=f"visitor-{index}",
                country_code="DK",
                country_name="Denmark",
                city="Copenhagen",
                latitude=55.6761,
                longitude=12.5683,
                path="/",
            )

        response = self.client.get(reverse("visitor_map_data"))

        self.assertEqual(response.status_code, 200)
        feature = response.json()["features"][0]
        self.assertEqual(feature["geometry"]["coordinates"], [12.6, 55.7])
        self.assertNotIn("city", feature["properties"])

    def test_map_data_is_served_from_cache_on_repeat_requests(self) -> None:
        self.client.get(reverse("visitor_map_data"))

        with self.assertNumQueries(0):
            response = self.client.get(reverse("visitor_map_data"))

        self.assertEqual(response.json(), {"type": "FeatureCollection", "features": []})

    def test_visitor_page_uses_the_keyless_openfreemap_basemap(self) -> None:
        """CARTO watermarks keyless tiles since September 2026; OpenFreeMap needs no key."""
        response = self.client.get(reverse("visitor_map"))

        self.assertContains(response, "https://tiles.openfreemap.org/styles/dark")
        self.assertNotContains(response, "basemaps.cartocdn.com")

    def test_visitor_page_renders_cached_summary(self) -> None:
        PageView.objects.create(
            timestamp=timezone.now(),
            ip_hash="visitor",
            country_code="DK",
            country_name="Denmark",
            latitude=55.6761,
            longitude=12.5683,
            path="/",
        )

        first = self.client.get(reverse("visitor_map"))
        with self.assertNumQueries(0):
            second = self.client.get(reverse("visitor_map"))

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.context["total_views"], 1)
        self.assertEqual(second.context["top_countries"][0]["country_code"], "DK")


class RequestLifecycleTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    @patch("core.tasks.complete_request_lifecycle.delay")
    def test_request_lifecycle_dispatches_a_task_for_a_valid_correlation_id(self, mock_delay) -> None:
        mock_delay.return_value.id = "12345678-1234-1234-1234-123456789012"

        response = self.client.post(
            reverse("request_lifecycle"),
            data='{"correlation_id": "12345678-1234-1234-1234-123456789012"}',
            content_type="application/json",
            HTTP_X_REAL_IP="203.0.113.10",
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["correlation_id"], "12345678-1234-1234-1234-123456789012")
        mock_delay.assert_called_once_with("12345678-1234-1234-1234-123456789012")

    def test_request_lifecycle_rejects_an_invalid_correlation_id(self) -> None:
        response = self.client.post(
            reverse("request_lifecycle"),
            data='{"correlation_id": "not-a-uuid"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("core.tasks.complete_request_lifecycle.delay")
    def test_request_lifecycle_throttles_repeated_requests_from_the_same_client(self, mock_delay) -> None:
        mock_delay.return_value.id = "12345678-1234-1234-1234-123456789012"
        payload = '{"correlation_id": "12345678-1234-1234-1234-123456789012"}'

        first_response = self.client.post(
            reverse("request_lifecycle"),
            data=payload,
            content_type="application/json",
            HTTP_X_REAL_IP="203.0.113.10",
        )
        second_response = self.client.post(
            reverse("request_lifecycle"),
            data=payload,
            content_type="application/json",
            HTTP_X_REAL_IP="203.0.113.10",
        )

        self.assertEqual(first_response.status_code, 202)
        self.assertEqual(second_response.status_code, 429)

    @patch("core.tasks.complete_request_lifecycle.delay")
    def test_rotating_x_forwarded_for_does_not_bypass_the_throttle(self, mock_delay) -> None:
        mock_delay.return_value.id = "12345678-1234-1234-1234-123456789012"
        payload = '{"correlation_id": "12345678-1234-1234-1234-123456789012"}'

        responses = [
            self.client.post(
                reverse("request_lifecycle"),
                data=payload,
                content_type="application/json",
                HTTP_X_FORWARDED_FOR=spoofed,
            )
            for spoofed in ("198.51.100.1", "198.51.100.2")
        ]

        self.assertEqual([r.status_code for r in responses], [202, 429])


class PresenceConsumerTests(SimpleTestCase):
    """Drives the consumer over raw ASGI; channels.testing would pull in daphne."""

    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    async def _connect(self, path: str) -> ApplicationCommunicator:
        scope = {"type": "websocket", "path": path, "headers": [], "query_string": b"", "subprotocols": []}
        communicator = ApplicationCommunicator(URLRouter(websocket_urlpatterns), scope)
        await communicator.send_input({"type": "websocket.connect"})
        self.assertEqual((await communicator.receive_output())["type"], "websocket.accept")
        return communicator

    async def _receive_count(self, communicator: ApplicationCommunicator) -> int:
        message = await communicator.receive_output()
        return int(json.loads(message["text"])["count"])

    async def test_count_tracks_connects_and_disconnects(self) -> None:
        first = await self._connect("/ws/presence/dashboard/")
        self.assertEqual(await self._receive_count(first), 1)

        second = await self._connect("/ws/presence/dashboard/")
        self.assertEqual(await self._receive_count(second), 2)
        self.assertEqual(await self._receive_count(first), 2)

        await second.send_input({"type": "websocket.disconnect", "code": 1000})
        await second.wait()
        self.assertEqual(await self._receive_count(first), 1)

        await first.send_input({"type": "websocket.disconnect", "code": 1000})
        await first.wait()
        self.assertEqual(await cache.aget("presence_count_dashboard"), 0)

    async def test_page_names_that_are_not_valid_group_names_are_rejected(self) -> None:
        scope = {"type": "websocket", "path": "/ws/presence/not valid!/", "headers": [], "query_string": b""}
        communicator = ApplicationCommunicator(URLRouter(websocket_urlpatterns), scope)
        await communicator.send_input({"type": "websocket.connect"})

        with self.assertRaises(ValueError):
            await communicator.wait()
