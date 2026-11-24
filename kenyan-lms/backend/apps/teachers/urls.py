"""Teacher routes (corrected ordering)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.teachers import views

router = DefaultRouter()
router.register("class-assignments", views.TeacherClassAssignmentViewSet, basename="teacherassignment")
router.register("lesson-plans", views.LessonPlanViewSet, basename="lessonplan")
router.register("", views.TeacherViewSet, basename="teacher")

urlpatterns = [path("", include(router.urls))]
