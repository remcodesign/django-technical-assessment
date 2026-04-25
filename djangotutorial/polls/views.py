from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie
from typing import cast

from .models import Question, QuestionManager
from .services import (
    DuplicateVote,
    InvalidChoice,
    MissingChoice,
    UserNotAuthenticated,
    cast_vote,
)


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last ten published questions."""
        # Keep the related choice count in SQL so the list page stays efficient.
        return cast(QuestionManager, Question.objects).with_choice_count().order_by("-pub_date")[:10]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


@ensure_csrf_cookie
def api_frontend(request):
    # The template reads the CSRF cookie in JavaScript, so we make sure it exists on first load.
    return render(
        request,
        "polls/api_frontend.html",
        {
            "api_base_url": reverse("polls_api:question-list"),
            "audit_base_url": reverse("polls_api:auditlog-list"),
        },
    )


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    try:
        cast_vote(request.user, question, request.POST.get("choice"))
    except UserNotAuthenticated:
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You must be logged in to vote.",
            },
        )
    except (MissingChoice, InvalidChoice):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    except DuplicateVote:
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
    return HttpResponseRedirect(reverse("polls:results", args=(question.pk,)))