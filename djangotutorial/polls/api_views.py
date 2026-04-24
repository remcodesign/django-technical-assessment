from django.db import IntegrityError, transaction
from django.db.models import F
from typing import cast
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Choice, Question, QuestionManager, UserVote
from .serializers import ChoiceSerializer, QuestionDetailSerializer, QuestionListSerializer
from .services import (
    DuplicateVote,
    InvalidChoice,
    MissingChoice,
    UserNotAuthenticated,
    cast_vote,
)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = cast(QuestionManager, Question.objects).with_choice_count().order_by("-pub_date")

    def get_queryset(self):  # type: ignore[override]
        if self.action in {"retrieve", "vote"}:
            return self.queryset.with_choices()
        return self.queryset

    def get_serializer_class(self):  # type: ignore[override]
        if self.action in {"retrieve", "vote"}:
            return QuestionDetailSerializer
        return QuestionListSerializer

    @action(detail=True, methods=["post"], url_path="vote")
    def vote(self, request, pk=None):
        question = self.get_object()

        try:
            cast_vote(request.user, question, request.data.get("choice"))
        except UserNotAuthenticated:
            return Response(
                {"error_message": "You must be logged in to vote."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except (MissingChoice, InvalidChoice):
            return Response(
                {"error_message": "You didn't select a choice."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DuplicateVote:
            return Response(
                {"error_message": "You already voted on this question."},
                status=status.HTTP_409_CONFLICT,
            )

        # Re-query so the response contains the fresh vote totals.
        fresh_question = Question.objects.with_choice_count().with_choices().get(pk=question.pk)
        return Response(QuestionDetailSerializer(fresh_question).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="choices")
    def add_choice(self, request, pk=None):
        question = self.get_object()
        serializer = ChoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(question=question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)