from django.db import migrations, models


def backfill_price_area(apps, schema_editor):
    """Set price_area='DK1' for all existing rows."""
    SpotPrice = apps.get_model("dashboard", "SpotPrice")
    SpotPrice.objects.filter(price_area="").update(price_area="DK1")


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0002_create_hypertable"),
    ]

    operations = [
        migrations.AddField(
            model_name="spotprice",
            name="price_area",
            field=models.CharField(
                max_length=3,
                choices=[("DK1", "DK1 (West Denmark)"), ("DK2", "DK2 (East Denmark)")],
                default="DK1",
            ),
        ),
        migrations.RunPython(backfill_price_area, migrations.RunPython.noop),
        migrations.RunSQL(
            sql="ALTER TABLE dashboard_spotprice DROP CONSTRAINT IF EXISTS dashboard_spotprice_pkey;",
            reverse_sql='ALTER TABLE dashboard_spotprice ADD PRIMARY KEY ("timestamp");',
        ),
        migrations.RunSQL(
            sql="""
                CREATE SEQUENCE IF NOT EXISTS dashboard_spotprice_id_seq;
                ALTER TABLE dashboard_spotprice
                    ADD COLUMN id BIGINT NOT NULL DEFAULT nextval('dashboard_spotprice_id_seq');
                ALTER SEQUENCE dashboard_spotprice_id_seq OWNED BY dashboard_spotprice.id;
            """,
            reverse_sql="""
                ALTER TABLE dashboard_spotprice DROP COLUMN IF EXISTS id;
                DROP SEQUENCE IF EXISTS dashboard_spotprice_id_seq;
            """,
        ),
        migrations.RunSQL(
            sql='CREATE UNIQUE INDEX uq_spotprice_id ON dashboard_spotprice (id, "timestamp");',
            reverse_sql="DROP INDEX IF EXISTS uq_spotprice_id;",
        ),
        migrations.RunSQL(
            sql='CREATE UNIQUE INDEX uq_spotprice_timestamp_area ON dashboard_spotprice ("timestamp", price_area);',
            reverse_sql="DROP INDEX IF EXISTS uq_spotprice_timestamp_area;",
        ),
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS dashboard_s_timesta_a23076_idx;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
