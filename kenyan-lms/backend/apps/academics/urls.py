"""Academic routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.academics import views

router = DefaultRouter()
router.register("timetable", views.TimetableEntryViewSet, basename="timetableentry")
router.register("events", views.SchoolEventViewSet, basename="schoolevent")

urlpatterns = [path("", include(router.urls))]
