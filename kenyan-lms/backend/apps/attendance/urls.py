"""Attendance routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.attendance import views

router = DefaultRouter()
router.register("", views.AttendanceRecordViewSet, basename="attendancerecord")

urlpatterns = [path("", include(router.urls))]
