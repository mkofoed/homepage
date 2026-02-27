import logging
import urllib.parse
from datetime import datetime
import httpx

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from dashboard.models import SpotPrice
from dashboard.services.energinet import ENERGINET_API_URL

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetches historical spot prices for DK1 and backfills the TimescaleDB hypertable."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=5000,
            help="Total number of historical records to fetch and insert.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        price_area = "DK1"
        self.stdout.write(f"Initiating backfill. Fetching {limit} records for {price_area}...")

        filter_val = f'{{"PriceArea":"{price_area}"}}'
        encoded_filter = urllib.parse.quote(filter_val)

        # Max limit per request is usually capped, so we could theoretically paginate, but
        # let's try a bulk pull first as their API supports large limits.
        url = f"{ENERGINET_API_URL}?limit={limit}&filter={encoded_filter}&sort=TimeUTC%20DESC"

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            self.stderr.write(f"Error fetching data: {e}")
            return

        records = data.get("records", [])
        if not records:
            self.stderr.write("No records found.")
            return

        self.stdout.write(f"Received {len(records)} records. Parsing...")

        spot_prices = []
        for record in records:
            timestamp_str = record.get("TimeUTC")
            if not timestamp_str:
                continue

            timestamp = parse_datetime(timestamp_str)
            if not timestamp:
                continue

            price_dkk = record.get("DayAheadPriceDKK")
            price_eur = record.get("DayAheadPriceEUR")
            if price_dkk is None or price_eur is None:
                continue

            spot_prices.append(
                SpotPrice(
                    timestamp=timestamp,
                    price_dkk=price_dkk,
                    price_eur=price_eur,
                )
            )

        if not spot_prices:
            self.stderr.write("No valid prices parsed from the records.")
            return

        # Bulk upsert ignores conflicts so we don't throw UniqueConstraint errors
        # if a price for a given timestamp already exists in the hypertable.
        self.stdout.write(f"Bulk inserting {len(spot_prices)} records into TimescaleDB...")
        inserted = SpotPrice.objects.bulk_create(spot_prices, ignore_conflicts=True, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f"Successfully inserted {len(inserted)} historical records!"))
