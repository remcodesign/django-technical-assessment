import json

from django.db.models import F
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import View, generic

from .models import Choice, Question


# Traditional Django Views

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("-pub_date")[:5]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
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
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

# API Views

def serialize_choice(choice):
    return {
        "id": choice.id,
        "choice_text": choice.choice_text,
        "votes": choice.votes,
    }


def serialize_question(question, include_choices=False):
    payload = {
        "id": question.id,
        "question_text": question.question_text,
        "pub_date": question.pub_date.isoformat(),
    }

    if include_choices:
        payload["choices"] = [serialize_choice(choice) for choice in question.choice_set.all()]

    return payload


class APIQuestionListView(View):
    def get(self, request):
        questions = Question.objects.order_by("-pub_date")
        data = [serialize_question(question) for question in questions]
        return JsonResponse({"results": data})

    def post(self, request):
        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        question_text = body.get("question_text")
        if not question_text:
            return JsonResponse({"error": "question_text is required"}, status=400)

        question = Question.objects.create(question_text=question_text, pub_date=timezone.now())
        return JsonResponse(serialize_question(question), status=201)


class APIQuestionDetailView(View):
    def get(self, request, pk):
        question = get_object_or_404(Question.objects.prefetch_related("choice_set"), pk=pk)
        return JsonResponse(serialize_question(question, include_choices=True))


class APIChoiceListView(View):
    def post(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)

        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        choice_text = body.get("choice_text")
        if not choice_text:
            return JsonResponse({"error": "choice_text is required"}, status=400)

        choice = Choice.objects.create(question=question, choice_text=choice_text)
        return JsonResponse(serialize_choice(choice), status=201)