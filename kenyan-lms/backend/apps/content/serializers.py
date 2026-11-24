"""Content serializers."""
from rest_framework import serializers

from apps.content.models import (
    Chapter, ContentAccess, ContentResource, DigitalTextbook, Exercise,
    ExerciseAttempt, Publisher,
)


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = "__all__"


class ChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = "__all__"


class ContentResourceSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ContentResource
        fields = "__all__"

    def get_file_url(self, obj):
        return obj.file.url if obj.file else obj.external_url


class ExerciseSerializer(serializers.ModelSerializer):
    attempt_count = serializers.IntegerField(source="attempts.count", read_only=True)

    class Meta:
        model = Exercise
        fields = "__all__"


class DigitalTextbookSerializer(serializers.ModelSerializer):
    publisher_name = serializers.CharField(source="publisher.name", read_only=True)
    chapter_count = serializers.IntegerField(source="chapters.count", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = DigitalTextbook
        fields = "__all__"


class TextbookDetailSerializer(DigitalTextbookSerializer):
    chapters = serializers.SerializerMethodField()

    def get_chapters(self, obj):
        chapters = obj.chapters.prefetch_related("exercises", "resources")
        return ChapterDetailSerializer(chapters, many=True).data


class ChapterDetailSerializer(ChapterSerializer):
    exercises = ExerciseSerializer(many=True, read_only=True)
    resources = ContentResourceSerializer(many=True, read_only=True)


class ExerciseAttemptSerializer(serializers.ModelSerializer):
    learner_name = serializers.CharField(source="learner.user.full_name", read_only=True)
    exercise_title = serializers.CharField(source="exercise.title", read_only=True)

    class Meta:
        model = ExerciseAttempt
        fields = "__all__"
        read_only_fields = ["institution"]


class ContentAccessSerializer(serializers.ModelSerializer):
    textbook_title = serializers.CharField(source="textbook.title", read_only=True)
    institution_name = serializers.CharField(source="institution.name", read_only=True)

    class Meta:
        model = ContentAccess
        fields = "__all__"
