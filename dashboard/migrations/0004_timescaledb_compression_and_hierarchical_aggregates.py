from django.db import migrations

FORWARD_SQL = """
ALTER TABLE dashboard_spotprice SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'price_area',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy(
    'dashboard_spotprice',
    compress_after => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_spotprice_hourly
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

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM dashboard_spotprice) THEN
        RAISE NOTICE 'No data exists; skipping refresh step';
        RETURN;
    END IF;
END $$;

CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_spotprice_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', bucket) AS bucket,
    price_area,
    SUM(avg_price_dkk * sample_count) / SUM(sample_count) AS avg_price_dkk,
    SUM(avg_price_eur * sample_count) / SUM(sample_count) AS avg_price_eur,
    MIN(min_price_dkk) AS min_price_dkk,
    MAX(max_price_dkk) AS max_price_dkk,
    SUM(sample_count) AS sample_count
FROM dashboard_spotprice_hourly
GROUP BY time_bucket('1 day', bucket), price_area
WITH NO DATA;


CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_spotprice_monthly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 month', bucket) AS bucket,
    price_area,
    SUM(avg_price_dkk * sample_count) / SUM(sample_count) AS avg_price_dkk,
    SUM(avg_price_eur * sample_count) / SUM(sample_count) AS avg_price_eur,
    MIN(min_price_dkk) AS min_price_dkk,
    MAX(max_price_dkk) AS max_price_dkk,
    SUM(sample_count) AS sample_count
FROM dashboard_spotprice_daily
GROUP BY time_bucket('1 month', bucket), price_area
WITH NO DATA;


CREATE MATERIALIZED VIEW IF NOT EXISTS dashboard_spotprice_yearly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 year', bucket) AS bucket,
    price_area,
    SUM(avg_price_dkk * sample_count) / SUM(sample_count) AS avg_price_dkk,
    SUM(avg_price_eur * sample_count) / SUM(sample_count) AS avg_price_eur,
    MIN(min_price_dkk) AS min_price_dkk,
    MAX(max_price_dkk) AS max_price_dkk,
    SUM(sample_count) AS sample_count
FROM dashboard_spotprice_monthly
GROUP BY time_bucket('1 year', bucket), price_area
WITH NO DATA;




SELECT add_continuous_aggregate_policy('dashboard_spotprice_hourly',
    start_offset => INTERVAL '7 days', end_offset => INTERVAL '2 hours',
    schedule_interval => INTERVAL '24 hours',
    initial_start => '2026-04-11 02:00:00+02'::timestamptz,
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('dashboard_spotprice_daily',
    start_offset => INTERVAL '14 days', end_offset => INTERVAL '2 hours',
    schedule_interval => INTERVAL '24 hours',
    initial_start => '2026-04-11 02:05:00+02'::timestamptz,
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('dashboard_spotprice_monthly',
    start_offset => INTERVAL '70 days', end_offset => INTERVAL '2 days',
    schedule_interval => INTERVAL '24 hours',
    initial_start => '2026-04-11 02:10:00+02'::timestamptz,
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('dashboard_spotprice_yearly',
    start_offset => INTERVAL '800 days', end_offset => INTERVAL '2 days'
    schedule_interval => INTERVAL '24 hours',
    initial_start => '2026-04-11 02:15:00+02'::timestamptz,
    if_not_exists => TRUE);
"""


REVERSE_SQL = """
SELECT remove_continuous_aggregate_policy('dashboard_spotprice_yearly', if_exists => TRUE);
SELECT remove_continuous_aggregate_policy('dashboard_spotprice_monthly', if_exists => TRUE);
SELECT remove_continuous_aggregate_policy('dashboard_spotprice_daily', if_exists => TRUE);
SELECT remove_continuous_aggregate_policy('dashboard_spotprice_hourly', if_exists => TRUE);
DROP MATERIALIZED VIEW IF EXISTS dashboard_spotprice_yearly CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dashboard_spotprice_monthly CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dashboard_spotprice_daily CASCADE;
DROP MATERIALIZED VIEW IF EXISTS dashboard_spotprice_hourly CASCADE;
SELECT remove_compression_policy('dashboard_spotprice', if_exists => TRUE);
SELECT decompress_chunk(c, if_compressed => TRUE) FROM show_chunks('dashboard_spotprice') c;
ALTER TABLE dashboard_spotprice SET (timescaledb.compress = FALSE);
"""


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("dashboard", "0003_add_price_area_and_surrogate_pk"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
    ]
