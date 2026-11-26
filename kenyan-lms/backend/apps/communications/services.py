"""Helpers for creating in-app notifications.

Notifications are created server-side only. Client requests cannot choose the
recipient through the API, so a user cannot send arbitrary alerts to someone
else. Preferences are honoured: a user who has disabled in-app notifications,
or has not subscribed to the event type, does not receive a row.
"""
from apps.communications.models import Notification, NotificationPreference


def notify_user(user, title, body="", notification_type="SYSTEM", link=""):
    """Create one in-app notification and return it, or ``None`` if suppressed."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    preference = NotificationPreference.objects.filter(user=user).first()
    if preference:
        if not preference.in_app:
            return None
        allowed_types = preference.types or []
        if allowed_types and notification_type not in allowed_types:
            return None
    return Notification.objects.create(
        recipient=user,
        title=title[:200],
        body=body,
        notification_type=notification_type,
        link=link[:300],
    )


def notify_users(users, title, body="", notification_type="SYSTEM", link=""):
    """Create notifications for several users, ignoring duplicate recipients."""
    created = []
    seen = set()
    for user in users:
        if not user or user.pk in seen:
            continue
        seen.add(user.pk)
        notification = notify_user(user, title, body, notification_type, link)
        if notification:
            created.append(notification)
    return created
