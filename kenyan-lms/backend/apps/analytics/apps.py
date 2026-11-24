"""Aggregation and rule-based remediation over existing school records. This is not a data warehouse product and does not train models; it stores computed snapshots for local reporting."""
from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    verbose_name = "Analytics and remediation"
