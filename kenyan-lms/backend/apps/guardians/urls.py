"""Guardian routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.guardians import views

router = DefaultRouter()
router.register("", views.GuardianViewSet, basename="guardian")

urlpatterns = [path("", include(router.urls))]
