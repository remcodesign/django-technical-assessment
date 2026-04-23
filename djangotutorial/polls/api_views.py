from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Question
from .serializers import ChoiceSerializer, QuestionDetailSerializer, QuestionListSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by("-pub_date")

    def get_queryset(self): 
        if self.action == "retrieve":
            return self.queryset.prefetch_related("choice_set")
        return self.queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuestionDetailSerializer
        return QuestionListSerializer

    @action(detail=True, methods=["post"], url_path="choices")
    def add_choice(self, request, pk=None):
        question = self.get_object()
        serializer = ChoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(question=question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)