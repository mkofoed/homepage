from datetime import UTC, datetime

from django.test import SimpleTestCase

from .services.energinet import _parse_utc_timestamp


class EnerginetTimestampTests(SimpleTestCase):
    def test_timestamp_is_converted_to_utc(self) -> None:
        timestamp = _parse_utc_timestamp("2026-07-19T10:00:00+02:00")

        self.assertEqual(timestamp, datetime(2026, 7, 19, 8, 0, tzinfo=UTC))

    def test_invalid_timestamp_is_skipped(self) -> None:
        self.assertIsNone(_parse_utc_timestamp("not-a-timestamp"))
