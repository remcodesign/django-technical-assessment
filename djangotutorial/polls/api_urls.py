from rest_framework.routers import DefaultRouter

from .api_views import AuditLogViewSet, QuestionViewSet

app_name = "polls_api"

router = DefaultRouter()
router.register("audit", AuditLogViewSet, basename="auditlog")
router.register("", QuestionViewSet, basename="question")

urlpatterns = router.urls