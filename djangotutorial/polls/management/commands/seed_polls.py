from django.core.management.base import BaseCommand
from django.utils import timezone

from polls.models import Choice, Question

# just a simple command to seed the database with one question and some choices, for testing purposes
class Command(BaseCommand):
    help = "Seed the polls app with one sample question and choices."

    def handle(self, *args, **options):
        question, created = Question.objects.get_or_create(
            question_text="What's up?",
            defaults={"pub_date": timezone.now()},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created question: {question}"))
        else:
            question.pub_date = timezone.now()
            question.save(update_fields=["pub_date"])
            self.stdout.write(self.style.WARNING(f"Updated existing question: {question}"))

        choices = [
            ("Not much", 0),
            ("The sky", 0),
            ("Just hacking again", 0),
        ]

        for choice_text, votes in choices:
            choice, choice_created = Choice.objects.get_or_create(
                question=question,
                choice_text=choice_text,
                defaults={"votes": votes},
            )
            if choice_created:
                self.stdout.write(self.style.SUCCESS(f"Created choice: {choice}"))
            else:
                self.stdout.write(self.style.WARNING(f"Choice already exists: {choice}"))

        self.stdout.write(self.style.SUCCESS("Polls seed complete."))
