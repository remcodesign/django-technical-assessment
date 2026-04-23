from rest_framework.routers import DefaultRouter

from .api_views import QuestionViewSet

app_name = "polls_api"

router = DefaultRouter()
router.register("", QuestionViewSet, basename="question")

urlpatterns = router.urls