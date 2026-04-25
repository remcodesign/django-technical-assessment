from rest_framework import serializers

from .models import Choice, Question


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "choice_text", "votes")
        read_only_fields = ("id", "votes")

    def validate_choice_text(self, value: str) -> str:
        question = self.context.get("question") or getattr(self.instance, "question", None)
        normalized = value.strip()

        if question is None:
            return normalized

        duplicates = Choice.objects.filter(question=question, choice_text__iexact=normalized)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)

        if duplicates.exists():
            raise serializers.ValidationError(
                "A choice with this text already exists for this question."
            )

        return normalized


class QuestionListSerializer(serializers.ModelSerializer):
    choice_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Question
        fields = ("id", "question_text", "pub_date", "choice_count")
        read_only_fields = ("id", "pub_date", "choice_count")


class QuestionDetailSerializer(QuestionListSerializer):
    user_choice_id = serializers.SerializerMethodField()
    choices = ChoiceSerializer(source="choice_set", many=True, read_only=True)

    class Meta(QuestionListSerializer.Meta):
        fields = QuestionListSerializer.Meta.fields + ("choices", "user_choice_id")

    def get_user_choice_id(self, question: Question) -> int | None:
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return None

        vote = question.user_votes.filter(user=request.user).select_related("choice").first()
        return vote.choice_id if vote is not None else None