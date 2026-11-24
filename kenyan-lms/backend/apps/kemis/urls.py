"""Local KEMIS-style export routes.

Local export staging only. Column names are a local approximation and must be checked against the current official KEMIS template before any submission. This app never transmits data to KEMIS and stores no credentials.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.kemis import views

router = DefaultRouter()
router.register("exports", views.KemisExportViewSet, basename="kemisexport")
router.register("mappings", views.KemisFieldMappingViewSet, basename="kemisfieldmapping")

urlpatterns = [path("", include(router.urls))]
