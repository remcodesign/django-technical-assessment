from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from ..models import AuditLog, Choice, Question

User = get_user_model()


def build_authenticated_csrf_client(username: str) -> tuple[APIClient, User, str]:
	user = User.objects.create_user(username=username, password="secret123")
	csrf_client = APIClient(enforce_csrf_checks=True)
	csrf_client.force_login(user)
	csrf_client.get(reverse("polls:api_frontend"))
	return csrf_client, user, csrf_client.cookies["csrftoken"].value


class AuditLogApiTests(TestCase):
	"""
	Integration tests for the audit log API endpoints.

	These tests ensure history browsing works end-to-end for the audit frontend:
	newest-first ordering, pagination, and filters for model, event, and user.
	"""

	def _create_audit_history(self) -> User:
		vote_client, vote_user, vote_csrf_token = build_authenticated_csrf_client("audit-voter")
		question_vote = Question.objects.create(question_text="Audit vote question")
		vote_choice = Choice.objects.create(question=question_vote, choice_text="Blue")

		vote_response = vote_client.post(
			reverse("polls_api:question-vote", kwargs={"pk": question_vote.pk}),
			{"choice": vote_choice.pk},
			format="json",
			HTTP_X_CSRFTOKEN=vote_csrf_token,
		)
		self.assertEqual(vote_response.status_code, 200)

		choice_client, _choice_user, choice_csrf_token = build_authenticated_csrf_client("audit-editor")
		question_choice = Question.objects.create(question_text="Audit choice question")

		create_response = choice_client.post(
			reverse("polls_api:question-add-choice", kwargs={"pk": question_choice.pk}),
			{"choice_text": "Original"},
			format="json",
			HTTP_X_CSRFTOKEN=choice_csrf_token,
		)
		self.assertEqual(create_response.status_code, 201)

		choice_id = create_response.data["id"]

		update_response = choice_client.patch(
			reverse(
				"polls_api:question-update-choice",
				kwargs={"pk": question_choice.pk, "choice_id": choice_id},
			),
			{"choice_text": "Updated"},
			format="json",
			HTTP_X_CSRFTOKEN=choice_csrf_token,
		)
		self.assertEqual(update_response.status_code, 200)

		delete_response = choice_client.delete(
			reverse(
				"polls_api:question-update-choice",
				kwargs={"pk": question_choice.pk, "choice_id": choice_id},
			),
			HTTP_X_CSRFTOKEN=choice_csrf_token,
		)
		self.assertEqual(delete_response.status_code, 204)

		self.assertEqual(AuditLog.objects.count(), 4)
		return vote_user

	def test_audit_log_list_orders_newest_first_and_paginates(self) -> None:
		"""
		Validate that the audit log list endpoint returns newest-first entries and supports pagination.

		How it works:
		1. Create a series of audit-producing actions (vote, create, update, delete).
		2. Query the audit log list with a small page size.
		3. Assert the newest entries appear first and pagination metadata is present.

		Why this matters:
		The audit frontend must show the latest activity first and allow browsing older
		entries without loading the entire history at once.
		"""
		self._create_audit_history()

		list_response = self.client.get(
			reverse("polls_api:auditlog-list"),
			{"page_size": 2},
		)

		self.assertEqual(list_response.status_code, 200)
		self.assertEqual(list_response.data["count"], 4)
		self.assertEqual(len(list_response.data["results"]), 2)
		self.assertIsNotNone(list_response.data["next"])
		self.assertIsNone(list_response.data["previous"])
		self.assertEqual(list_response.data["results"][0]["actor"], "audit-editor")
		self.assertEqual(list_response.data["results"][0]["model"], "Choice")
		self.assertEqual(list_response.data["results"][0]["event"], "delete")

		second_page = self.client.get(
			reverse("polls_api:auditlog-list"),
			{"page_size": 2, "page": 2},
		)

		self.assertEqual(second_page.status_code, 200)
		self.assertEqual(len(second_page.data["results"]), 2)
		self.assertIsNotNone(second_page.data["previous"])

	def test_audit_log_list_filters_by_model_and_event(self) -> None:
		"""
		Validate that the audit log list endpoint can filter by model and event.

		How it works:
		1. Create a history of audit entries across different models and events.
		2. Query the list endpoint with a model filter, then an event filter.
		3. Assert the results only contain entries matching each filter.

		Why this matters:
		Users should be able to narrow audit history to relevant domains and actions.
		"""
		vote_user = self._create_audit_history()

		choice_only_response = self.client.get(
			reverse("polls_api:auditlog-list"),
			{"model": "Choice", "page_size": 10},
		)

		self.assertEqual(choice_only_response.status_code, 200)
		self.assertEqual(choice_only_response.data["count"], 3)
		self.assertTrue(all(entry["model"] == "Choice" for entry in choice_only_response.data["results"]))

		vote_only_response = self.client.get(
			reverse("polls_api:auditlog-list"),
			{"event": "vote", "page_size": 10},
		)

		self.assertEqual(vote_only_response.status_code, 200)
		self.assertEqual(vote_only_response.data["count"], 1)
		self.assertEqual(vote_only_response.data["results"][0]["actor"], vote_user.username)
		self.assertEqual(vote_only_response.data["results"][0]["model"], "UserVote")
		self.assertEqual(vote_only_response.data["results"][0]["event"], "vote")

	def test_audit_log_list_filters_by_user(self) -> None:
		"""
		Validate that the audit log list endpoint can filter by user.

		How it works:
		1. Create a history of audit entries including a vote by a specific user.
		2. Query the list endpoint with that user's name.
		3. Assert only entries for that actor are returned.

		Why this matters:
		The audit frontend needs to support quick lookup of a single user's activity.
		"""
		vote_user = self._create_audit_history()

		user_only_response = self.client.get(
			reverse("polls_api:auditlog-list"),
			{"user": vote_user.username, "page_size": 10},
		)

		self.assertEqual(user_only_response.status_code, 200)
		self.assertEqual(user_only_response.data["count"], 1)
		self.assertEqual(user_only_response.data["results"][0]["actor"], vote_user.username)
