"""Communication routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.communications import views

router = DefaultRouter()
router.register("announcements", views.AnnouncementViewSet, basename="announcement")
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("messages", views.MessageViewSet, basename="message")
router.register("preferences", views.NotificationPreferenceViewSet, basename="notificationpreference")

urlpatterns = [path("", include(router.urls))]
