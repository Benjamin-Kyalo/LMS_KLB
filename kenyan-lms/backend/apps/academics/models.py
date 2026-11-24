"""Timetables and school events."""
from django.db import models

from apps.core.models import InstitutionScopedModel


class TimetableEntry(InstitutionScopedModel):
    DAYS = [
        ("MONDAY", "Monday"), ("TUESDAY", "Tuesday"), ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"), ("FRIDAY", "Friday"), ("SATURDAY", "Saturday"),
        ("SUNDAY", "Sunday"),
    ]

    school_class = models.ForeignKey("institutions.SchoolClass", on_delete=models.CASCADE, related_name="timetable_entries")
    term = models.ForeignKey("institutions.Term", on_delete=models.CASCADE, related_name="timetable_entries")
    subject = models.ForeignKey("institutions.Subject", on_delete=models.CASCADE)
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.SET_NULL, null=True, blank=True)
    day_of_week = models.CharField(max_length=10, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time} - {self.subject}"


class SchoolEvent(InstitutionScopedModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(
        max_length=30, default="OTHER",
        choices=[("EXAM", "Examination"), ("HOLIDAY", "Holiday"), ("MEETING", "Meeting"),
                 ("SPORTS", "Sports"), ("OTHER", "Other")],
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["start_datetime"]
