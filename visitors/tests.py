from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from .middleware import VisitorTrackingMiddleware
from .services.geoip import _get_reader, lookup_ip


class GeoIpLookupTests(SimpleTestCase):
    def tearDown(self) -> None:
        _get_reader.cache_clear()

    def test_lookup_uses_the_local_maxmind_database(self) -> None:
        reader = Mock()
        reader.get.return_value = {
            "country": {"iso_code": "DK", "names": {"en": "Denmark"}},
            "city": {"names": {"en": "Copenhagen"}},
            "location": {"latitude": 55.6761, "longitude": 12.5683},
        }

        with TemporaryDirectory() as directory:
            Path(directory, "GeoLite2-City.mmdb").touch()
            with override_settings(GEOIP_PATH=directory):
                with patch("visitors.services.geoip.open_database", return_value=reader) as open_database:
                    location = lookup_ip("203.0.113.10")

        self.assertIsNotNone(location)
        assert location is not None
        self.assertEqual(location.country_code, "DK")
        self.assertEqual(location.city, "Copenhagen")
        open_database.assert_called_once()
        reader.get.assert_called_once_with("203.0.113.10")


class VisitorTrackingMiddlewareTests(SimpleTestCase):
    @patch("visitors.tasks.log_page_view")
    def test_uses_the_proxy_address_not_a_client_supplied_forwarded_header(self, log_page_view: Mock) -> None:
        request = RequestFactory().get(
            "/",
            HTTP_USER_AGENT="Mozilla/5.0",
            HTTP_X_FORWARDED_FOR="198.51.100.1",
            HTTP_X_REAL_IP="203.0.113.10",
        )

        response = VisitorTrackingMiddleware(lambda _: HttpResponse())(request)

        self.assertEqual(response.status_code, 200)
        log_page_view.delay.assert_called_once_with(ip="203.0.113.10", path="/", device_type="desktop")
