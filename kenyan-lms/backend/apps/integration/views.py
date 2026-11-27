"""Read-only, OneRoster-shaped views for pinned external school systems.

Only published, institution-scoped records are exposed. The responses are
familiar OneRoster shapes, but this is groundwork: there is no provisioning,
no LTI launch, no OIDC/JWKS and no OAuth token endpoint.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes, throttle_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.audit import log_audit
from apps.core.constants import ContentStatus
from apps.courses.models import Course, LessonProgress, Submission
from apps.institutions.models import Institution
from apps.integration.auth import OneRosterAssertionAuthentication
from apps.integration.permissions import HasOneRosterScope
from apps.integration.throttling import (
    IntegrationUnsupportedThrottle, OneRosterThrottle,
)
from apps.learners.models import Learner
from apps.teachers.models import Teacher


def _source_id(record, fallback_prefix):
    """Return a stable business identifier without exposing model internals."""
    for field in ("reference", "code", "admission_number", "staff_number"):
        value = getattr(record, field, "")
        if value:
            return str(value)
    return f"{fallback_prefix}-{record.pk}"


def _institution(principal):
    institution = Institution.objects.filter(
        pk=principal.institution_id, is_active=True
    ).first()
    if institution is None:
        raise PermissionDenied("This client is not linked to an active institution.")
    return institution


def _bounded_int(request, name, default, minimum, maximum=None):
    try:
        value = int(request.query_params.get(name, default))
    except (TypeError, ValueError):
        value = default
    value = max(minimum, value)
    return min(value, maximum) if maximum is not None else value


def _audit_read(request, resource, scope, returned, total, limit, offset):
    """Record the read without writing any personal data into audit details."""
    principal = request.user
    log_audit(
        None,
        "integration.oneroster.read",
        "OneRosterResource",
        resource,
        {
            "client_id": principal.client_id,
            "scope": scope,
            "limit": limit,
            "offset": offset,
            "returned": returned,
            "total": total,
        },
        institution=principal.institution_id,
        request=request,
    )


def _paged_response(request, rows, resource_key, scope):
    maximum = int(getattr(settings, "ONEROSTER_MAX_PAGE_SIZE", 100))
    limit = _bounded_int(request, "limit", 50, 1, maximum)
    offset = _bounded_int(request, "offset", 0, 0)
    total = len(rows)
    page = rows[offset:offset + limit]
    _audit_read(request, resource_key, scope, len(page), total, limit, offset)
    return Response({
        resource_key: page,
        "paging": {"offset": offset, "limit": limit, "total": total},
    })


class OneRosterReadOnlyView(APIView):
    """Shared authentication, scoping, throttling, paging and audit for GETs."""

    authentication_classes = [OneRosterAssertionAuthentication]
    permission_classes = [HasOneRosterScope]
    throttle_classes = [OneRosterThrottle]
    resource_key = ""
    oneroster_scope = ""

    def get(self, request, *args, **kwargs):
        institution = _institution(request.user)
        rows = self.build_rows(request.user, institution)
        return _paged_response(request, rows, self.resource_key, self.oneroster_scope)

    def build_rows(self, principal, institution):
        raise NotImplementedError


class CoursesView(OneRosterReadOnlyView):
    resource_key = "courses"
    oneroster_scope = "courses.read"

    def build_rows(self, principal, institution):
        courses = Course.objects.filter(
            institution=institution, status=ContentStatus.PUBLISHED
        ).select_related("subject", "academic_year", "term").order_by("pk")
        return [{
            "sourcedId": _source_id(course, "course"),
            "status": "active",
            "title": course.title,
            "orgSourcedId": institution.code,
            "metadata": {
                "code": course.code,
                "subject": course.subject.name if course.subject_id else "",
                "academicYear": course.academic_year.name if course.academic_year_id else "",
                "term": course.term.name if course.term_id else "",
            },
        } for course in courses]


class ClassesView(OneRosterReadOnlyView):
    resource_key = "classes"
    oneroster_scope = "classes.read"

    def build_rows(self, principal, institution):
        courses = Course.objects.filter(
            institution=institution, status=ContentStatus.PUBLISHED
        ).select_related("term").order_by("pk")
        return [{
            "sourcedId": _source_id(course, "course"),
            "status": "active",
            "title": course.title,
            "classCode": course.code,
            "courseSourcedId": _source_id(course, "course"),
            "orgSourcedId": institution.code,
            "termSourcedId": course.term.name if course.term_id else "",
        } for course in courses]


class UsersView(OneRosterReadOnlyView):
    resource_key = "users"
    oneroster_scope = "users.read"

    def build_rows(self, principal, institution):
        rows = []
        learners = Learner.objects.filter(
            institution=institution, status="ACTIVE", is_archived=False
        ).select_related("user").order_by("pk")
        for learner in learners:
            user = learner.user
            rows.append({
                "sourcedId": f"student-{_source_id(learner, 'student')}",
                "status": "active",
                "role": "student",
                "username": user.username,
                "givenName": user.first_name,
                "familyName": user.last_name,
                "email": user.email,
                "orgSourcedId": institution.code,
            })
        teachers = Teacher.objects.filter(
            institution=institution, is_active=True, is_archived=False
        ).select_related("user").order_by("pk")
        for teacher in teachers:
            user = teacher.user
            rows.append({
                "sourcedId": f"teacher-{_source_id(teacher, 'teacher')}",
                "status": "active",
                "role": "teacher",
                "username": user.username,
                "givenName": user.first_name,
                "familyName": user.last_name,
                "email": user.email,
                "orgSourcedId": institution.code,
            })
        rows.sort(key=lambda row: row["sourcedId"])
        return rows


def _enrollment(role, user_sourced_id, course, institution):
    class_sourced_id = _source_id(course, "course")
    return {
        "sourcedId": f"enrollment-{role}-{user_sourced_id}-{class_sourced_id}",
        "status": "active",
        "userId": user_sourced_id,
        "role": role,
        "classSourcedId": class_sourced_id,
        "orgSourcedId": institution.code,
    }


class EnrollmentsView(OneRosterReadOnlyView):
    resource_key = "enrollments"
    oneroster_scope = "enrollments.read"

    def build_rows(self, principal, institution):
        course_queryset = Course.objects.filter(
            institution=institution, status=ContentStatus.PUBLISHED
        ).select_related("teacher").order_by("pk")
        courses = {course.pk: course for course in course_queryset}
        course_ids = list(courses)
        rows = []

        # Teachers are enrolled from the published course owner field.
        for course in courses.values():
            teacher = course.teacher
            if (
                teacher is not None
                and teacher.institution_id == institution.pk
                and teacher.is_active
                and not teacher.is_archived
            ):
                rows.append(_enrollment(
                    "teacher",
                    f"teacher-{_source_id(teacher, 'teacher')}",
                    course,
                    institution,
                ))

        # This schema has no separate enrollment table. Learner membership is
        # derived from lesson progress and submissions in published courses.
        pairs = set()
        if course_ids:
            pairs.update(
                LessonProgress.objects.filter(
                    institution=institution, lesson__module__course_id__in=course_ids
                ).values_list("learner_id", "lesson__module__course_id").distinct()
            )
            pairs.update(
                Submission.objects.filter(
                    institution=institution, assignment__course_id__in=course_ids
                ).values_list("learner_id", "assignment__course_id").distinct()
            )
        learner_ids = {learner_id for learner_id, _ in pairs}
        learners = {
            learner.pk: learner
            for learner in Learner.objects.filter(
                pk__in=learner_ids, institution=institution,
                status="ACTIVE", is_archived=False,
            )
        }
        for learner_id, course_id in sorted(pairs):
            learner = learners.get(learner_id)
            course = courses.get(course_id)
            if learner is None or course is None:
                continue
            rows.append(_enrollment(
                "student", f"student-{_source_id(learner, 'student')}", course, institution
            ))

        rows.sort(key=lambda row: row["sourcedId"])
        return rows


class OrgsView(OneRosterReadOnlyView):
    resource_key = "orgs"
    oneroster_scope = "orgs.read"

    def build_rows(self, principal, institution):
        return [{
            "sourcedId": institution.code,
            "status": "active",
            "name": institution.name,
            "type": "school",
        }]


@api_view(["GET", "POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([IntegrationUnsupportedThrottle])
def unsupported_integration(request, feature):
    """Explicitly close protocol surfaces this groundwork does not implement."""
    log_audit(
        None,
        "integration.unsupported.rejected",
        "IntegrationFeature",
        feature,
        {"feature": feature, "method": request.method},
        request=request,
    )
    return Response({
        "code": "unsupported_integration",
        "message": "This integration method is not supported by this application.",
    }, status=status.HTTP_403_FORBIDDEN)
