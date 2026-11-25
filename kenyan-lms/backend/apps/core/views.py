"""Health check used by both humans and monitoring tools."""
import logging

from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Report whether the API and the database are reachable."""
    database_ok = True
    error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # pragma: no cover - only fails when DB is down
        database_ok = False
        logger.exception("Database health probe failed")
        error = "Database unavailable"

    return Response(
        {
            "status": "ok" if database_ok else "error",
            "service": "KLB Digital Learning Ecosystem",
            "database": "connected" if database_ok else "unavailable",
            "error": error,
        },
        status=200 if database_ok else 503,
    )
