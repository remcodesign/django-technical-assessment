from django.shortcuts import get_object_or_404
from typing import cast
from django.db import transaction
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import AuditLog, Choice, Question, QuestionManager
from .serializers import (
    AuditLogSerializer,
    ChoiceSerializer,
    QuestionDetailSerializer,
    QuestionListSerializer,
    VoteSerializer,
)
from .services import (
    DuplicateVote,
    InvalidChoice,
    MissingChoice,
    UserNotAuthenticated,
    cast_vote,
    format_audit_change,
    record_audit_event,
)

# The question viewset handles both the question list and detail endpoints since they share most of the same logic, 
# and the serializer dynamically adjusts based on the action for optimal query performance.
# The vote and choice management endpoints are implemented as custom actions on the question viewset since they operate on the question resource and require similar context for permissions and response payloads.

class QuestionViewSet(viewsets.ModelViewSet):
    # The base queryset is empty since the list and detail views require different annotations for optimal performance.
    queryset = Question.objects.none()

    def get_permissions(self):  # type: ignore[override]
        if self.action in {"add_choice", "update_choice"}:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]

        return [permission() for permission in permission_classes]

    def _fresh_detail_payload(self, question: Question):
        # Re-query the question so the response always includes the latest nested choices and counts.
        question_manager = cast(QuestionManager, Question.objects)
        fresh_question = question_manager.with_choice_count().with_choices().get(pk=question.pk)
        return QuestionDetailSerializer(
            fresh_question,
            context=self.get_serializer_context(),
        ).data

    def get_queryset(self):  # type: ignore[override]
        queryset = cast(QuestionManager, Question.objects).with_choice_count().order_by("-pub_date")
        if self.action == "list":
            return queryset[:20]
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
        serializer = VoteSerializer(data=request.data, question=question)

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            return Response(
                {"error_message": "You didn't select a choice."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        choice = serializer.validated_data["choice"]

        try:
            cast_vote(request.user, question, choice.pk)
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

        with transaction.atomic():
            choice = serializer.save(question=question)
            record_audit_event(
                request.user,
                model_name="Choice",
                object_id=choice.pk,
                event="create",
                change_to=format_audit_change(
                    choice_text=choice.choice_text,
                    question_id=question.pk,
                ),
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path=r"choices/(?P<choice_id>[^/.]+)")
    def update_choice(self, request, pk=None, choice_id=None):
        question = self.get_object()
        choice = get_object_or_404(Choice, pk=choice_id, question=question)
        previous_choice_text = choice.choice_text
        serializer = ChoiceSerializer(
            choice,
            data=request.data,
            partial=True,
            context={"question": question},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            choice = serializer.save()
            record_audit_event(
                request.user,
                model_name="Choice",
                object_id=choice.pk,
                event="update",
                change_from=format_audit_change(choice_text=previous_choice_text),
                change_to=format_audit_change(choice_text=choice.choice_text),
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @update_choice.mapping.delete  # type: ignore[attr-defined]
    def delete_choice(self, request, pk=None, choice_id=None):
        question = self.get_object()
        choice = get_object_or_404(Choice, pk=choice_id, question=question)

        with transaction.atomic():
            previous_choice_text = choice.choice_text
            choice.delete()
            record_audit_event(
                request.user,
                model_name="Choice",
                object_id=choice_id,
                event="delete",
                change_from=format_audit_change(choice_text=previous_choice_text),
                change_to=format_audit_change(deleted=True),
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
    
# The audit log is read-only, so we can use a simpler viewset with just the list mixin.

class AuditLogPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 25


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    pagination_class = AuditLogPagination

    def get_queryset(self):  # type: ignore[override]
        queryset = AuditLog.objects.select_related("user").order_by("-created_at", "-pk")
        query_params = getattr(self.request, "query_params", {})
        user_filter = query_params.get("user")
        model_filter = query_params.get("model")
        event_filter = query_params.get("event")

        if user_filter:
            queryset = queryset.filter(user__username__iexact=user_filter.strip())

        if model_filter:
            queryset = queryset.filter(model__iexact=model_filter.strip())

        if event_filter:
            queryset = queryset.filter(event__iexact=event_filter.strip())

        return queryset

    @action(detail=False, methods=["get"], url_path="users")
    def users(self, request):
        usernames = (
            AuditLog.objects.filter(user__isnull=False)
            .order_by("user__username")
            .values_list("user__username", flat=True)
            .distinct()
        )
        return Response(list(usernames))