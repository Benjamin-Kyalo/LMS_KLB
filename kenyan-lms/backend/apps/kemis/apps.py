"""Local KEMIS-style export staging.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.
"""
from django.apps import AppConfig


class KemisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.kemis"
    verbose_name = "KEMIS-style exports (local staging only)"
