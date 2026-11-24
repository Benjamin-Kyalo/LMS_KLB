"""Curriculum routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.curriculum import views

router = DefaultRouter()
router.register("frameworks", views.CurriculumFrameworkViewSet, basename="curriculumframework")
router.register("levels", views.EducationLevelViewSet, basename="educationlevel")
router.register("learning-areas", views.LearningAreaViewSet, basename="learningarea")
router.register("strands", views.StrandViewSet, basename="strand")
router.register("sub-strands", views.SubStrandViewSet, basename="substrand")
router.register("outcomes", views.LearningOutcomeViewSet, basename="learningoutcome")
router.register("competencies", views.CompetencyViewSet, basename="competency")
router.register("rubrics", views.RubricViewSet, basename="rubric")
router.register("rubric-levels", views.RubricLevelViewSet, basename="rubriclevel")
router.register("evidence", views.CompetencyEvidenceViewSet, basename="competencyevidence")

urlpatterns = [path("", include(router.urls))]
