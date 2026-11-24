"""Curriculum-grounded learning assistant. By default it is fully local and deterministic; an optional HTTP provider can be configured with environment variables, but no credentials are bundled and no external service is contacted unless explicitly configured."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.tutor import views

router = DefaultRouter()
router.register("conversations", views.TutorConversationViewSet, basename="tutorconversation")
router.register("messages", views.TutorMessageViewSet, basename="tutormessage")

urlpatterns = [path("", include(router.urls))]
