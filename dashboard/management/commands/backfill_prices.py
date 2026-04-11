import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date

from dashboard.services.energinet import fetch_spot_prices_for_range

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Backfill Energinet spot prices for a given date range. Defaults to current month."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-date",
            type=str,
            help="Start date in ISO format (YYYY-MM-DD). Defaults to start of current month.",
        )
        parser.add_argument(
            "--to-date",
            type=str,
            help="End date in ISO format (YYYY-MM-DD). Defaults to today.",
        )

    def handle(self, *args, **options):
        from_date = options["from_date"]
        to_date = options["to_date"]

        # Default to start of the current month and today
        today = date.today()
        if not from_date:
            from_date = today.replace(day=1).isoformat()
        if not to_date:
            to_date = today.isoformat()

        # Validate dates
        start_date = parse_date(from_date) or parse_date(from_date + "T00:00")
        end_date = parse_date(to_date) or parse_date(to_date + "T00:00")
        if not start_date or not end_date:
            raise CommandError("Invalid date formats. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM.")
        if start_date > end_date:
            raise CommandError("'from-date' cannot be later than 'to-date'.")

        logger.info(f"Starting backfill for range {start_date} -> {end_date}.")

        try:
            price_areas = ["DK1", "DK2"]
            total_inserted = 0
            delta = timedelta(days=7)  # Chunk by week
            current_start = start_date

            while current_start <= end_date:
                current_end = min(current_start + delta, end_date + timedelta(days=1))

                for area in price_areas:
                    logger.info(f"Fetching spot prices for {area} in range {current_start} -> {current_end}...")
                    inserted = fetch_spot_prices_for_range(
                        start_date=current_start.isoformat(), end_date=current_end.isoformat(), price_area=area
                    )
                    total_inserted += inserted

                    logger.info(f"Inserted {inserted} records for {area} in range {current_start} -> {current_end}.")
                current_start += delta

            logger.info(f"Backfill complete. Total records inserted: {total_inserted}.")
            self.stdout.write(self.style.SUCCESS(f"Successfully backfilled {total_inserted} spot prices."))
        except Exception as e:
            logger.exception("Failed to backfill spot prices.")
            raise CommandError(f"Error during backfill: {e}") from e
