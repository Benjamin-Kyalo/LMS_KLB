"""Root URL configuration. Each app owns its own /api/... routes."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", core_views.health_check, name="health-check"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/institutions/", include("apps.institutions.urls")),
    path("api/learners/", include("apps.learners.urls")),
    path("api/teachers/", include("apps.teachers.urls")),
    path("api/guardians/", include("apps.guardians.urls")),
    path("api/academics/", include("apps.academics.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/curriculum/", include("apps.curriculum.urls")),
    path("api/courses/", include("apps.courses.urls")),
    path("api/assessments/", include("apps.assessments.urls")),
    path("api/content/", include("apps.content.urls")),
    path("api/communications/", include("apps.communications.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/fees/", include("apps.fees.urls")),
    path("api/approval/", include("apps.approval.urls")),
    path("api/kemis/", include("apps.kemis.urls")),
    path("api/tutor/", include("apps.tutor.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/theming/", include("apps.theming.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
