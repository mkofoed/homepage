# Generated for visitors app

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PageView",
            fields=[
                ("timestamp", models.DateTimeField(primary_key=True, serialize=False)),
                ("ip_hash", models.CharField(max_length=64)),
                ("country_code", models.CharField(max_length=2)),
                ("country_name", models.CharField(max_length=100)),
                ("city", models.CharField(max_length=100, blank=True, default="")),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                ("path", models.CharField(max_length=500)),
                (
                    "device_type",
                    models.CharField(
                        max_length=10,
                        choices=[("desktop", "Desktop"), ("mobile", "Mobile"), ("tablet", "Tablet")],
                        default="desktop",
                    ),
                ),
            ],
            options={
                "db_table": "page_views",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.RunSQL(
            sql=[
                "CREATE EXTENSION IF NOT EXISTS timescaledb;",
                "SELECT create_hypertable('page_views', 'timestamp', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);",
                "CREATE INDEX idx_pageview_country ON page_views (country_code, timestamp DESC);",
                "CREATE INDEX idx_pageview_ip_hash ON page_views (ip_hash, timestamp DESC);",
                "SELECT add_retention_policy('page_views', INTERVAL '90 days', if_not_exists => TRUE);",
            ],
            reverse_sql=["DROP TABLE IF EXISTS page_views CASCADE;"],
        ),
    ]
