import json

from django.db import IntegrityError, transaction
from django.db.models import F

from .models import AuditLog, Choice, Question, UserVote


class VoteError(Exception):
    pass


class UserNotAuthenticated(VoteError):
    pass


class MissingChoice(VoteError):
    pass


class InvalidChoice(VoteError):
    pass


class DuplicateVote(VoteError):
    pass


def format_audit_change(**payload) -> str:
    if not payload:
        return ""

    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def record_audit_event(
    user,
    *,
    model_name: str,
    object_id,
    event: str,
    change_from: str = "",
    change_to: str = "",
) -> AuditLog:
    return AuditLog.objects.create(
        user=user,
        model=model_name,
        object_id=str(object_id),
        event=event,
        change_from=change_from,
        change_to=change_to,
    )


def cast_vote(user, question: Question, choice_id):
    if not user.is_authenticated:
        raise UserNotAuthenticated("You must be logged in to vote.")

    if not choice_id:
        raise MissingChoice("You didn't select a choice.")

    try:
        selected_choice = Choice.objects.get(question=question, pk=choice_id)
    except Choice.DoesNotExist:
        raise InvalidChoice("You didn't select a choice.")

    try:
        with transaction.atomic():
            current_votes = selected_choice.votes
            user_vote = UserVote.objects.create(
                user=user,
                choice=selected_choice,
                question=question,
            )
            selected_choice.votes = F("votes") + 1
            selected_choice.save(update_fields=["votes"])
            record_audit_event(
                user,
                model_name="UserVote",
                object_id=user_vote.pk,
                event="vote",
                change_to=format_audit_change(
                    choice_id=selected_choice.pk,
                    choice_text=selected_choice.choice_text,
                    question_id=question.pk,
                    votes_before=current_votes,
                    votes_after=current_votes + 1,
                ),
            )
    except IntegrityError as exc:
        raise DuplicateVote("You already voted on this question.") from exc

    return selected_choice
