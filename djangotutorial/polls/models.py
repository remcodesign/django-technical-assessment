import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    # auto_now_add sets the field to now when the object is first created.
    pub_date = models.DateTimeField("date published", auto_now_add=True)

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        # Returns True if the question was published within the last day.
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


class UserVote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="poll_votes",
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name="user_votes",
    )
    # Keep question explicit so the database can enforce one vote per user per question.
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="user_votes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "question"),
                name="unique_user_vote_per_question",
            ),
        ]

    def __str__(self):
        return f"{self.user} voted for {self.choice} on {self.question}"