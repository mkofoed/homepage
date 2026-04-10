from django.db import migrations

FORWARD_SQL = """
-- Step 1: Enable compression
ALTER TABLE dashboard_spotprice SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'price_area',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Step 2: Compression policy (compress chunks older than 7 days)
SELECT add_compression_policy(
    'dashboard_spotprice',
    compress_after => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Step 3: Continuous aggregate for hourly rollups
CREATE MATERIALIZED VIEW dashboard_spotprice_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', "timestamp") AS bucket,
    price_area,
    AVG(price_dkk) AS avg_price_dkk,
    AVG(price_eur) AS avg_price_eur,
    MIN(price_dkk) AS min_price_dkk,
    MAX(price_dkk) AS max_price_dkk,
    COUNT(*) AS sample_count
FROM dashboard_spotprice
GROUP BY time_bucket('1 hour', "timestamp"), price_area
WITH NO DATA;

-- Step 4: Backfill existing data
CALL refresh_continuous_aggregate('dashboard_spotprice_hourly', NULL, NOW());

-- Step 5: Refresh policy (last 3 days, every 24h, starting 02:00 CEST)
SELECT add_continuous_aggregate_policy(
    'dashboard_spotprice_hourly',
    start_offset    => INTERVAL '3 days',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '24 hours',
    initial_start   => '2026-04-11 02:00:00+02'::timestamptz,
    timezone        => 'Europe/Copenhagen',
    if_not_exists   => TRUE
);
"""


REVERSE_SQL = """
SELECT remove_continuous_aggregate_policy('dashboard_spotprice_hourly', if_exists => TRUE);
DROP MATERIALIZED VIEW IF EXISTS dashboard_spotprice_hourly CASCADE;
SELECT remove_compression_policy('dashboard_spotprice', if_exists => TRUE);
SELECT decompress_chunk(c, if_compressed => TRUE)
FROM show_chunks('dashboard_spotprice') c;
ALTER TABLE dashboard_spotprice SET (timescaledb.compress = FALSE);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0002_create_hypertable"),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD_SQL,
            reverse_sql=REVERSE_SQL,
        ),
    ]
