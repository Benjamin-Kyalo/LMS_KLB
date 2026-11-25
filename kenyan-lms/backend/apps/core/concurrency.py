"""Structured conflict responses for concurrent web writes.

Two layers:

* ``conflict_exception_handler`` is installed globally. It turns a database
  uniqueness/foreign-key failure into a structured HTTP 409 instead of a 500,
  so the web client receives a conflict it can surface to the user and retry
  deliberately.
* ``ConflictAwareMixin`` is opt-in. When a client sends ``If-Match`` with the
  ``updated_at`` value it originally loaded, a stale PATCH/PUT/DELETE returns
  409 with the current server representation. Clients that do not send
  ``If-Match`` keep the existing last-write-wins behaviour.
"""
from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

CONFLICT_CODE = "conflict"


def conflict_response(message, server=None):
    body = {"code": CONFLICT_CODE, "message": message}
    if server is not None:
        body["server"] = server
    return Response(body, status=status.HTTP_409_CONFLICT)


def conflict_exception_handler(exc, context):
    """DRF exception handler that maps IntegrityError to a safe 409."""
    if isinstance(exc, IntegrityError):
        # Never echo the raw database message: it can expose table and column
        # names and, in some drivers, fragments of submitted values.
        return conflict_response("This record conflicts with an existing record.")
    return drf_exception_handler(exc, context)


class ConflictAwareMixin:
    """Opt-in optimistic concurrency based on ``updated_at`` and ``If-Match``."""

    conflict_serializer_class = None

    def _conflict_serializer(self, instance):
        serializer_class = self.conflict_serializer_class or self.get_serializer_class()
        return serializer_class(instance, context=self.get_serializer_context())

    def _stale_conflict(self, instance, request):
        if instance is None or not hasattr(instance, "updated_at"):
            return None
        expected = request.headers.get("If-Match") or request.META.get("HTTP_IF_MATCH")
        if not expected:
            return None
        expected = expected.strip().strip('"')
        actual = instance.updated_at.isoformat()
        if expected == actual:
            return None
        return conflict_response("This record changed since you loaded it.", {
            "id": instance.pk,
            "updated_at": actual,
            "data": self._conflict_serializer(instance).data,
        })

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return conflict_response("This record already exists.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        stale = self._stale_conflict(instance, request)
        if stale is not None:
            return stale
        try:
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, "_prefetched_objects_cache", None):
                instance._prefetched_objects_cache = {}
            return Response(serializer.data)
        except IntegrityError:
            return conflict_response("This record conflicts with an existing record.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        stale = self._stale_conflict(instance, request)
        if stale is not None:
            return stale
        try:
            return super().destroy(request, *args, **kwargs)
        except IntegrityError:
            return conflict_response("This record is still referenced by other records.")
