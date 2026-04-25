from django.shortcuts import get_object_or_404
from typing import cast
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Choice, Question, QuestionManager
from .serializers import ChoiceSerializer, QuestionDetailSerializer, QuestionListSerializer
from .services import (
    DuplicateVote,
    InvalidChoice,
    MissingChoice,
    UserNotAuthenticated,
    cast_vote,
)


class QuestionViewSet(viewsets.ModelViewSet):
    # The base queryset is empty since the list and detail views require different annotations for optimal performance.
    queryset = Question.objects.none()

    def _fresh_detail_payload(self, question: Question):
        # Re-query the question so the response always includes the latest nested choices and counts.
        fresh_question = Question.objects.with_choice_count().with_choices().get(pk=question.pk)
        return QuestionDetailSerializer(
            fresh_question,
            context=self.get_serializer_context(),
        ).data

    def get_queryset(self):  # type: ignore[override]
        queryset = cast(QuestionManager, Question.objects).with_choice_count().order_by("-pub_date")
        if self.action in {"retrieve", "vote"}:
            return queryset.with_choices()
        return queryset

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

        return Response(self._fresh_detail_payload(question), status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="choices")
    def add_choice(self, request, pk=None):
        question = self.get_object()
        serializer = ChoiceSerializer(data=request.data, context={"question": question})
        serializer.is_valid(raise_exception=True)
        serializer.save(question=question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path=r"choices/(?P<choice_id>[^/.]+)")
    def update_choice(self, request, pk=None, choice_id=None):
        question = self.get_object()
        choice = get_object_or_404(Choice, pk=choice_id, question=question)
        serializer = ChoiceSerializer(
            choice,
            data=request.data,
            partial=True,
            context={"question": question},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @update_choice.mapping.delete
    def delete_choice(self, request, pk=None, choice_id=None):
        question = self.get_object()
        choice = get_object_or_404(Choice, pk=choice_id, question=question)
        choice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)