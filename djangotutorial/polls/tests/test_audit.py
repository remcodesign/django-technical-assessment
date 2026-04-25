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
	def test_audit_log_list_paginates_filters_and_orders_newest_first(self) -> None:
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

		delete_response = choice_client.delete(
			reverse(
				"polls_api:question-update-choice",
				kwargs={"pk": question_choice.pk, "choice_id": choice_id},
			),
			HTTP_X_CSRFTOKEN=choice_csrf_token,
		)

		self.assertEqual(create_response.status_code, 201)
		self.assertEqual(update_response.status_code, 200)
		self.assertEqual(delete_response.status_code, 204)
		self.assertEqual(AuditLog.objects.count(), 4)

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

		user_only_response = self.client.get(
			reverse("polls_api:auditlog-list"),
			{"user": vote_user.username, "page_size": 10},
		)

		self.assertEqual(user_only_response.status_code, 200)
		self.assertEqual(user_only_response.data["count"], 1)
		self.assertEqual(user_only_response.data["results"][0]["actor"], vote_user.username)
