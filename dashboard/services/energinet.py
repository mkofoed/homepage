import logging
import urllib.parse
from datetime import datetime

import httpx
from django.utils.dateparse import parse_datetime

from dashboard.models import SpotPrice

logger = logging.getLogger(__name__)

ENERGINET_API_URL = "https://api.energidataservice.dk/dataset/DayAheadPrices"


def fetch_latest_spot_prices(limit: int = 24, price_area: str = "DK1") -> int:
    """
    Fetches the latest spot prices from Energi Data Service and saves them to the
    TimescaleDB hypertable. Returns the number of new records inserted.
    """
    filter_val = f'{{"PriceArea":"{price_area}"}}'
    encoded_filter = urllib.parse.quote(filter_val)
    url = f"{ENERGINET_API_URL}?limit={limit}&filter={encoded_filter}&sort=TimeUTC%20DESC"

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.RequestError as e:
        logger.error(f"Error fetching data from Energi Data Service: {e}")
        return 0

    records = data.get("records", [])
    if not records:
        logger.warning(f"No records found for {price_area} in Energi Data Service response.")
        return 0

    # Parse and bulk-upsert records
    spot_prices = []
    for record in records:
        timestamp_str = record.get("TimeUTC")
        if not timestamp_str:
            continue

        timestamp = parse_datetime(timestamp_str)
        if timestamp is None:
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
        return 0

    # Bulk create, ignoring conflicts (if a record for this timestamp already exists)
    inserted = SpotPrice.objects.bulk_create(spot_prices, ignore_conflicts=True)

    return len(inserted)
