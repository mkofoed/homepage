from django.db import models


class PageView(models.Model):
    timestamp = models.DateTimeField(primary_key=True)
    ip_hash = models.CharField(max_length=64)
    country_code = models.CharField(max_length=2)
    country_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, default="")
    latitude = models.FloatField()
    longitude = models.FloatField()
    path = models.CharField(max_length=500)
    device_type = models.CharField(
        max_length=10,
        choices=[("desktop", "Desktop"), ("mobile", "Mobile"), ("tablet", "Tablet")],
        default="desktop",
    )

    class Meta:
        db_table = "page_views"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.city}, {self.country_code} — {self.path} @ {self.timestamp}"
