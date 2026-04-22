from django.urls import path

from . import views

app_name = "polls_api"

urlpatterns = [
    path("", views.APIQuestionListView.as_view(), name="question-list"),
    path("<int:pk>/", views.APIQuestionDetailView.as_view(), name="question-detail"),
    path("<int:question_id>/choices/", views.APIChoiceListView.as_view(), name="choice-list"),
]