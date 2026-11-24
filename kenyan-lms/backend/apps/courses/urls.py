"""Course routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.courses import views

router = DefaultRouter()
# Specific prefixes must come before the catch-all empty prefix.
router.register("modules", views.ModuleViewSet, basename="module")
router.register("lessons", views.LessonViewSet, basename="lesson")
router.register("progress", views.LessonProgressViewSet, basename="lessonprogress")
router.register("assignments", views.AssignmentViewSet, basename="assignment")
router.register("submissions", views.SubmissionViewSet, basename="submission")
router.register("", views.CourseViewSet, basename="course")

urlpatterns = [path("", include(router.urls))]
