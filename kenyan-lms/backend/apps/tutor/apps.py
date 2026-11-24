"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
from django.apps import AppConfig


class TutorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tutor"
    verbose_name = "Curriculum-grounded tutor"
