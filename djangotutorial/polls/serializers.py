from rest_framework import serializers

from .models import Choice, Question


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "choice_text", "votes")
        read_only_fields = ("id", "votes")


class QuestionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("id", "question_text", "pub_date")
        read_only_fields = ("id", "pub_date")


class QuestionDetailSerializer(QuestionListSerializer):
    choices = ChoiceSerializer(source="choice_set", many=True, read_only=True)

    class Meta(QuestionListSerializer.Meta):
        fields = QuestionListSerializer.Meta.fields + ("choices",)