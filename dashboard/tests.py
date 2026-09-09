"""Tests for the electricity-price dashboard.

The value in this app is the tariff arithmetic, and its edge cases are all
calendar edge cases: N1 charges different rates by season and time of day, and
Denmark observes DST, so a UTC timestamp and its Copenhagen local hour drift
apart for half the year. AGENTS.md requires DST-sensitive behavior to be
covered whenever the energy calculations change; this file pins the
winter/summer season and day/night/peak hour boundaries that the tariff
lookup depends on. It does NOT yet exercise the DST changeover days
themselves (2026-03-29, 2026-10-25) -- see the tracked follow-up on
get_chart_data's fixed 96-slot day skeleton, which is suspected to mishandle
23- and 25-hour local days.

`SpotPrice` is a TimescaleDB hypertable in production; under the test settings
it is an ordinary SQLite table, which is enough to exercise the query and
aggregation logic but not the hypertable SQL itself.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import httpx
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from dashboard.models import PriceArea, SpotPrice
from dashboard.services.current_price import _total_price, get_current_price
from dashboard.services.energinet import _parse_utc_timestamp, fetch_latest_spot_prices
from dashboard.services.price_chart import (
    DK_ELAFGIFT,
    DK_ELSPAREBIDRAG,
    DK_ENERGINET_TARIFF,
    DK_VAT_MULTIPLIER,
    N1_GRID_TARIFFS,
    _grid_tariff_ex_vat,
    _period_bounds,
    _to_cph,
    get_chart_data,
)


class EnerginetTimestampTests(SimpleTestCase):
    def test_timestamp_is_converted_to_utc(self) -> None:
        timestamp = _parse_utc_timestamp("2026-07-19T10:00:00+02:00")

        self.assertEqual(timestamp, datetime(2026, 7, 19, 8, 0, tzinfo=UTC))

    def test_invalid_timestamp_is_skipped(self) -> None:
        self.assertIsNone(_parse_utc_timestamp("not-a-timestamp"))

    def test_naive_timestamp_is_assumed_to_be_utc(self) -> None:
        """Energinet's TimeUTC field is naive; reading it as local time would shift prices by two hours."""
        timestamp = _parse_utc_timestamp("2026-07-19T10:00:00")

        self.assertEqual(timestamp, datetime(2026, 7, 19, 10, 0, tzinfo=UTC))


class GridTariffTests(SimpleTestCase):
    """N1 time-of-use bands, expressed in Copenhagen local time."""

    def test_winter_and_summer_seasons_split_on_the_documented_months(self) -> None:
        # October through March is winter; April through September is summer.
        winter = _grid_tariff_ex_vat(datetime(2026, 3, 15, 12, 0, tzinfo=UTC))
        summer = _grid_tariff_ex_vat(datetime(2026, 4, 15, 12, 0, tzinfo=UTC))

        self.assertEqual(winter, N1_GRID_TARIFFS["winter"]["day"])
        self.assertEqual(summer, N1_GRID_TARIFFS["summer"]["day"])
        self.assertGreater(winter, summer)

    def test_peak_band_covers_seventeen_to_twentyone_copenhagen_time(self) -> None:
        # 16:00 CET is 15:00 UTC in winter; 17:00 CET is 16:00 UTC.
        before_peak = _grid_tariff_ex_vat(datetime(2026, 1, 15, 15, 30, tzinfo=UTC))
        in_peak = _grid_tariff_ex_vat(datetime(2026, 1, 15, 16, 30, tzinfo=UTC))
        after_peak = _grid_tariff_ex_vat(datetime(2026, 1, 15, 20, 30, tzinfo=UTC))

        self.assertEqual(before_peak, N1_GRID_TARIFFS["winter"]["day"])
        self.assertEqual(in_peak, N1_GRID_TARIFFS["winter"]["peak"])
        self.assertEqual(after_peak, N1_GRID_TARIFFS["winter"]["day"])

    def test_night_band_covers_midnight_to_six_copenhagen_time(self) -> None:
        # 03:00 CET is 02:00 UTC in winter.
        night = _grid_tariff_ex_vat(datetime(2026, 1, 15, 2, 0, tzinfo=UTC))

        self.assertEqual(night, N1_GRID_TARIFFS["winter"]["night"])

    def test_summer_time_offset_is_applied_when_choosing_the_band(self) -> None:
        """In July, Copenhagen is UTC+2. 15:30 UTC is 17:30 local, so it is peak.

        Reading the UTC hour directly would classify it as the cheaper day band.
        """
        self.assertEqual(
            _grid_tariff_ex_vat(datetime(2026, 7, 15, 15, 30, tzinfo=UTC)),
            N1_GRID_TARIFFS["summer"]["peak"],
        )
        # The same wall-clock UTC hour in January is only UTC+1, so still day rate.
        self.assertEqual(
            _grid_tariff_ex_vat(datetime(2026, 1, 15, 15, 30, tzinfo=UTC)),
            N1_GRID_TARIFFS["winter"]["day"],
        )

    def test_bands_are_ordered_peak_above_day_above_night(self) -> None:
        for season, bands in N1_GRID_TARIFFS.items():
            with self.subTest(season=season):
                self.assertGreater(bands["peak"], bands["day"])
                self.assertGreater(bands["day"], bands["night"])


class TotalPriceTests(SimpleTestCase):
    def test_total_is_spot_plus_taxes_and_tariffs_including_vat(self) -> None:
        timestamp = datetime(2026, 1, 15, 2, 0, tzinfo=UTC)  # winter night band

        total = _total_price(Decimal("500"), timestamp)

        expected = (
            Decimal("500") / 1000
            + DK_ELAFGIFT
            + DK_ELSPAREBIDRAG
            + DK_ENERGINET_TARIFF
            + N1_GRID_TARIFFS["winter"]["night"]
        ) * DK_VAT_MULTIPLIER
        self.assertEqual(total, expected)

    def test_a_negative_spot_price_can_still_yield_a_positive_total(self) -> None:
        """Negative day-ahead prices are real; tariffs are charged regardless."""
        timestamp = datetime(2026, 1, 15, 2, 0, tzinfo=UTC)
        total = _total_price(Decimal("-50"), timestamp)

        expected = (
            Decimal("-50") / 1000
            + DK_ELAFGIFT
            + DK_ELSPAREBIDRAG
            + DK_ENERGINET_TARIFF
            + N1_GRID_TARIFFS["winter"]["night"]
        ) * DK_VAT_MULTIPLIER
        self.assertEqual(total, expected)
        self.assertGreater(total, 0)


class PeriodBoundsTests(SimpleTestCase):
    def test_day_window_starts_at_copenhagen_midnight(self) -> None:
        now = datetime(2026, 7, 15, 13, 45, tzinfo=UTC)  # 15:45 local

        start, end, label = _period_bounds("day", now)

        self.assertEqual(_to_cph(start).hour, 0)
        self.assertEqual(_to_cph(start).day, 15)
        self.assertEqual((end - start).days, 1)
        self.assertIn("2026", label)

    def test_an_unknown_range_falls_back_to_the_week_window(self) -> None:
        now = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)

        unknown = _period_bounds("fortnight", now)
        week = _period_bounds("week", now)

        self.assertEqual(unknown, week)

    def test_offset_shifts_the_day_window_backwards(self) -> None:
        now = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)

        start_today, _, _ = _period_bounds("day", now)
        start_yesterday, _, _ = _period_bounds("day", now, offset=-1)

        self.assertEqual((start_today - start_yesterday).days, 1)


class CurrentPriceTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def _create_hour(self, hour_start: datetime, price_dkk: str, price_area: str = PriceArea.DK1) -> None:
        """Four quarter-hour records, as Energinet publishes them."""
        for quarter in range(4):
            SpotPrice.objects.create(
                timestamp=hour_start.replace(minute=quarter * 15),
                price_area=price_area,
                price_dkk=Decimal(price_dkk),
                price_eur=Decimal(price_dkk) / Decimal("7.45"),
            )

    def test_returns_none_when_no_prices_exist(self) -> None:
        self.assertIsNone(get_current_price(datetime(2026, 1, 15, 12, 0, tzinfo=UTC)))

    def test_current_hour_is_averaged_across_its_quarters(self) -> None:
        hour = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        for quarter, price in enumerate(["300", "400", "500", "400"]):
            SpotPrice.objects.create(
                timestamp=hour.replace(minute=quarter * 15),
                price_area=PriceArea.DK1,
                price_dkk=Decimal(price),
                price_eur=Decimal("1"),
            )

        context = get_current_price(hour.replace(minute=37))

        assert context is not None
        self.assertEqual(context.hour_start, hour)
        self.assertFalse(context.stale)
        # Average spot is 400 DKK/MWh -> 0.40 DKK/kWh ex VAT -> 0.50 incl VAT.
        self.assertEqual(context.spot_price, Decimal("0.50"))

    def test_missing_current_hour_falls_back_to_the_latest_hour_and_marks_it_stale(self) -> None:
        self._create_hour(datetime(2026, 1, 15, 8, 0, tzinfo=UTC), "500")

        context = get_current_price(datetime(2026, 1, 15, 12, 30, tzinfo=UTC))

        assert context is not None
        self.assertTrue(context.stale)
        self.assertEqual(context.hour_start, datetime(2026, 1, 15, 8, 0, tzinfo=UTC))

    def test_price_areas_do_not_leak_into_each_other(self) -> None:
        hour = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        self._create_hour(hour, "400", PriceArea.DK1)
        self._create_hour(hour, "800", PriceArea.DK2)

        # No cache.clear() between calls: the cache key includes price_area, so
        # if that were ever dropped, DK2's request would wrongly hit DK1's
        # cached entry instead of querying fresh -- exactly what this test
        # exists to catch.
        dk1 = get_current_price(hour, price_area=PriceArea.DK1)
        dk2 = get_current_price(hour, price_area=PriceArea.DK2)

        assert dk1 is not None and dk2 is not None
        self.assertLess(dk1.current_price, dk2.current_price)

    def test_trend_is_unavailable_without_a_comparison_hour(self) -> None:
        hour = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        self._create_hour(hour, "500")

        context = get_current_price(hour)

        assert context is not None
        self.assertEqual(context.trend_direction, "unavailable")
        self.assertIsNone(context.trend_pct)

    def test_trend_compares_against_the_same_hour_yesterday(self) -> None:
        hour = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        self._create_hour(hour - timedelta(days=1), "200")
        self._create_hour(hour, "600")

        context = get_current_price(hour)

        assert context is not None
        self.assertEqual(context.trend_direction, "up")
        assert context.trend_pct is not None
        self.assertGreater(context.trend_pct, 0)

    def test_result_is_cached_so_a_second_call_does_not_requery(self) -> None:
        hour = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        self._create_hour(hour, "500")

        first = get_current_price(hour)
        SpotPrice.objects.all().delete()
        second = get_current_price(hour)

        self.assertEqual(first, second)


class ChartDataTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def test_day_view_is_padded_to_a_full_ninety_six_quarter_skeleton(self) -> None:
        """A partial day must still render a full 00:00-23:45 axis, with gaps as null."""
        day_start_utc = datetime(2026, 1, 14, 23, 0, tzinfo=UTC)  # 2026-01-15 00:00 CET
        SpotPrice.objects.create(
            timestamp=day_start_utc,
            price_area=PriceArea.DK1,
            price_dkk=Decimal("500"),
            price_eur=Decimal("67"),
        )

        chart = get_chart_data("day", datetime(2026, 1, 15, 12, 0, tzinfo=UTC))

        self.assertEqual(len(chart.labels), 96)
        self.assertEqual(len(chart.data_total), 96)
        self.assertIsNotNone(chart.data_total[0])
        self.assertIsNone(chart.data_total[1])

    def test_total_is_the_sum_of_the_two_stacked_components(self) -> None:
        SpotPrice.objects.create(
            timestamp=datetime(2026, 1, 14, 23, 0, tzinfo=UTC),
            price_area=PriceArea.DK1,
            price_dkk=Decimal("500"),
            price_eur=Decimal("67"),
        )

        chart = get_chart_data("day", datetime(2026, 1, 15, 12, 0, tzinfo=UTC))

        # Independently derived from the public tariff constants (not from
        # chart.data_elpris/data_transport themselves) so a bug in the VAT or
        # tariff arithmetic can't cancel out and still pass.
        expected_elpris = float((Decimal("500") / 1000) * DK_VAT_MULTIPLIER) + float(
            (DK_ELAFGIFT + DK_ELSPAREBIDRAG) * DK_VAT_MULTIPLIER
        )
        expected_transport = float(DK_ENERGINET_TARIFF * DK_VAT_MULTIPLIER) + float(
            N1_GRID_TARIFFS["winter"]["night"] * DK_VAT_MULTIPLIER
        )
        self.assertAlmostEqual(chart.data_total[0], round(expected_elpris + expected_transport, 4), places=3)
        self.assertAlmostEqual(
            chart.data_total[0],
            chart.data_elpris[0] + chart.data_transport[0],
            places=3,
        )

    def test_empty_range_returns_an_empty_but_well_formed_result(self) -> None:
        chart = get_chart_data("week", datetime(2026, 1, 15, 12, 0, tzinfo=UTC))

        self.assertEqual(chart.data_total, [])
        self.assertTrue(chart.period_label)


class EnerginetIngestionTests(TestCase):
    """Ingestion must be idempotent and must fail closed when the API misbehaves."""

    def _response(self, records: list[dict]) -> httpx.Response:
        return httpx.Response(
            200,
            json={"records": records},
            request=httpx.Request("GET", "https://api.energidataservice.dk/"),
        )

    @patch("httpx.Client.get")
    def test_records_are_persisted(self, mock_get) -> None:
        mock_get.return_value = self._response(
            [
                {
                    "TimeUTC": "2026-01-15T12:00:00",
                    "DayAheadPriceDKK": 500.0,
                    "DayAheadPriceEUR": 67.0,
                    "PriceArea": "DK1",
                }
            ]
        )

        inserted = fetch_latest_spot_prices()

        self.assertEqual(inserted, 1)
        self.assertEqual(SpotPrice.objects.count(), 1)

    @patch("httpx.Client.get")
    def test_ingesting_the_same_interval_twice_updates_rather_than_duplicates(self, mock_get) -> None:
        """The (timestamp, price_area) unique constraint makes re-runs safe."""
        mock_get.return_value = self._response(
            [
                {
                    "TimeUTC": "2026-01-15T12:00:00",
                    "DayAheadPriceDKK": 500.0,
                    "DayAheadPriceEUR": 67.0,
                    "PriceArea": "DK1",
                }
            ]
        )
        fetch_latest_spot_prices()

        mock_get.return_value = self._response(
            [
                {
                    "TimeUTC": "2026-01-15T12:00:00",
                    "DayAheadPriceDKK": 750.0,
                    "DayAheadPriceEUR": 100.0,
                    "PriceArea": "DK1",
                }
            ]
        )
        fetch_latest_spot_prices()

        self.assertEqual(SpotPrice.objects.count(), 1)
        self.assertEqual(SpotPrice.objects.get().price_dkk, Decimal("750.00"))

    @patch("httpx.Client.get")
    def test_dk1_and_dk2_are_stored_separately_for_the_same_interval(self, mock_get) -> None:
        mock_get.return_value = self._response(
            [
                {
                    "TimeUTC": "2026-01-15T12:00:00",
                    "DayAheadPriceDKK": 500.0,
                    "DayAheadPriceEUR": 67.0,
                    "PriceArea": "DK1",
                },
                {
                    "TimeUTC": "2026-01-15T12:00:00",
                    "DayAheadPriceDKK": 600.0,
                    "DayAheadPriceEUR": 80.0,
                    "PriceArea": "DK2",
                },
            ]
        )

        fetch_latest_spot_prices()

        self.assertEqual(SpotPrice.objects.count(), 2)

    @patch("httpx.Client.get")
    def test_records_with_missing_fields_are_skipped_not_stored_as_null(self, mock_get) -> None:
        mock_get.return_value = self._response(
            [
                {"TimeUTC": "2026-01-15T12:00:00", "DayAheadPriceEUR": 67.0, "PriceArea": "DK1"},
                {"DayAheadPriceDKK": 500.0, "DayAheadPriceEUR": 67.0, "PriceArea": "DK1"},
                {
                    "TimeUTC": "2026-01-15T13:00:00",
                    "DayAheadPriceDKK": 500.0,
                    "DayAheadPriceEUR": 67.0,
                    "PriceArea": "DK1",
                },
            ]
        )

        inserted = fetch_latest_spot_prices()

        self.assertEqual(inserted, 1)
        self.assertEqual(SpotPrice.objects.count(), 1)

    @patch("httpx.Client.get", side_effect=httpx.ConnectError("upstream is down"))
    def test_a_network_failure_returns_zero_instead_of_raising(self, mock_get) -> None:
        """The Celery beat schedule calls this; an exception here would fail the task run."""
        self.assertEqual(fetch_latest_spot_prices(), 0)
        self.assertEqual(SpotPrice.objects.count(), 0)

    @patch("httpx.Client.get")
    def test_an_empty_payload_returns_zero(self, mock_get) -> None:
        mock_get.return_value = self._response([])

        self.assertEqual(fetch_latest_spot_prices(), 0)


class DashboardViewTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def test_dashboard_renders_without_any_price_data(self) -> None:
        """An empty database is the state right after a fresh deploy."""
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
