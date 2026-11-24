"""Content routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content import views

router = DefaultRouter()
router.register("publishers", views.PublisherInfoViewSet, basename="publisher")
router.register("textbooks", views.DigitalTextbookViewSet, basename="digitaltextbook")
router.register("chapters", views.ChapterViewSet, basename="chapter")
router.register("resources", views.ContentResourceViewSet, basename="contentresource")
router.register("exercises", views.ExerciseViewSet, basename="exercise")
router.register("exercise-attempts", views.ExerciseAttemptViewSet, basename="exerciseattempt")
router.register("access", views.ContentAccessViewSet, basename="contentaccess")
router.register("available", views.AvailableTextbookViewSet, basename="availabletextbook")

urlpatterns = [path("", include(router.urls))]
