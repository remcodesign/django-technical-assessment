from django.db import IntegrityError, transaction
from django.db.models import F

from .models import Choice, Question, UserVote


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
            UserVote.objects.create(
                user=user,
                choice=selected_choice,
                question=question,
            )
            selected_choice.votes = F("votes") + 1
            selected_choice.save(update_fields=["votes"])
    except IntegrityError as exc:
        raise DuplicateVote("You already voted on this question.") from exc

    return selected_choice
