from __future__ import annotations

import random

from celery import shared_task
from django.utils import timezone

from .models import Choice, Question


CONFIGS = {
    'standard': (
        'What is your favorite',
        'Which tool do you prefer for',
        'How would you rate',
    ),
    'smoke': (
        'Smoke test question',
        'Quick validation question',
        'One minute check',
    ),
}

CHOICE_LABELS = ('Option A', 'Option B', 'Option C')


def _persist_poll(prefixes: tuple[str, ...], *, include_minute: bool = False) -> int:
    """Internal helper to build and save the Poll objects."""
    stamp_format = '%Y%m%d%H%M' if include_minute else '%Y%m%d%H'
    question_text = f"{random.choice(prefixes)} Celery phase {timezone.now().strftime(stamp_format)}?"

    question = Question.objects.create(question_text=question_text)
    Choice.objects.bulk_create(
        [
            Choice(question=question, choice_text=f"{label} for {question_text[:24]}")
            for label in CHOICE_LABELS
        ]
    )

    return question.pk


@shared_task(name='polls.tasks.create_hourly_question')
def create_hourly_question() -> int:
    return _persist_poll(CONFIGS['standard'])

# for testing purposes, a task that creates a question every minute with a different set of prefixes to distinguish them from the hourly questions. 
# Commented out in the beat schedule to avoid cluttering the database during development, but can be enabled for testing.
@shared_task(name='polls.tasks.create_smoke_question')
def create_smoke_question() -> int:
    return _persist_poll(CONFIGS['smoke'], include_minute=True)