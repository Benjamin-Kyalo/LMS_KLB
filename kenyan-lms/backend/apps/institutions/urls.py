"""Institution routes (corrected ordering)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.institutions import views

router = DefaultRouter()
router.register("public-institutions", views.PublicInstitutionViewSet, basename="public-institution")
router.register("types", views.InstitutionTypeViewSet, basename="institutiontype")
router.register("departments", views.DepartmentViewSet, basename="department")
router.register("academic-years", views.AcademicYearViewSet, basename="academicyear")
router.register("terms", views.TermViewSet, basename="term")
router.register("classes", views.SchoolClassViewSet, basename="schoolclass")
router.register("subjects", views.SubjectViewSet, basename="subject")
router.register("", views.InstitutionViewSet, basename="institution")

urlpatterns = [path("", include(router.urls))]
