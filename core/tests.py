from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Post
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
