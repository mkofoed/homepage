import logging
from django.core.management.base import BaseCommand
from dashboard.services.energinet import fetch_latest_spot_prices

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Polls the Energi Data Service for the latest DK1 spot prices (meant to run hourly)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=24,
            help="Number of hours to pull. Defaults to 24 to catch up on any missed hours.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        self.stdout.write(f"Polling Energi Data Service for the latest {limit} spot prices...")

        inserted = fetch_latest_spot_prices(limit=limit)

        if inserted > 0:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully polled and inserted {inserted} new spot price records!")
            )
        else:
            self.stdout.write("Poll successful, but no new records were inserted (all recent data already exists).")
