from django.db import IntegrityError, transaction
from django.db.models import Count, F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Choice, Question, UserVote


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last ten published questions."""
        # Keep the related choice count in SQL so the list page stays efficient.
        return Question.objects.annotate(choice_count=Count("choice")).order_by("-pub_date")[:10]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    # Require login to vote, but allow anyone to view the question and results.
    if not request.user.is_authenticated:
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You must be logged in to vote.",
            },
        )
    
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )

    try:
        # Use a transaction to ensure that the vote is recorded atomically
        with transaction.atomic():
            # Store the individual vote explicitly and keep the existing counter in sync.
            UserVote.objects.create(
                user=request.user,
                choice=selected_choice,
                question=question,
            )
            # the original code - as a cache of the votes
            selected_choice.votes = F("votes") + 1
            selected_choice.save(update_fields=["votes"])
    except IntegrityError:
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You already voted on this question.",
            },
        )

    # Always return an HttpResponseRedirect after successfully dealing
    # with POST data. This prevents data from being posted twice if a
    # user hits the Back button.
    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))