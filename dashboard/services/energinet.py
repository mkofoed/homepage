import logging
import urllib.parse

import httpx
from django.utils.dateparse import parse_datetime

from dashboard.models import SpotPrice

logger = logging.getLogger(__name__)

ENERGINET_API_URL = "https://api.energidataservice.dk/dataset/Elspotprices"


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

    # Bulk upsert to handle both new records and updates for existing timestamps
    SpotPrice.objects.bulk_create(
        spot_prices, update_conflicts=True, update_fields=["price_dkk", "price_eur"], unique_fields=["timestamp"]
    )

    logger.info(f"Upserted {len(spot_prices)} spot prices. Potentially updated existing entries.")
    return len(spot_prices)


def fetch_spot_prices_for_range(start_date: str, end_date: str, price_area: str = "DK1") -> int:
    """
    Fetches spot prices from Energi Data Service for a specific date range and saves them.
    Returns the number of new records inserted.
    """
    params = urllib.parse.urlencode(
        {"filter": f'{{"PriceArea":"{price_area}"}}', "start": start_date, "end": end_date, "sort": "TimeUTC ASC"}
    )
    url = f"{ENERGINET_API_URL}?{params}"

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

    # Parse and bulk-insert records
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

    SpotPrice.objects.bulk_create(
        spot_prices, update_conflicts=True, update_fields=["price_dkk", "price_eur"], unique_fields=["timestamp"]
    )

    logger.info(f"Upserted {len(spot_prices)} spot prices for range {start_date} -> {end_date}.")
    return len(spot_prices)
