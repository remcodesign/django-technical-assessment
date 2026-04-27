from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from typing import Any

from rest_framework.test import APIClient

from ..models import AuditLog, Choice, Question, UserVote

User = get_user_model()


def build_authenticated_csrf_client(username: str) -> tuple[APIClient, str]:
	user = User.objects.create_user(username=username, password="secret123")
	csrf_client = APIClient(enforce_csrf_checks=True)
	csrf_client.force_login(user)
	csrf_client.get(reverse("polls:api_frontend"))
	return csrf_client, csrf_client.cookies["csrftoken"].value


class PollsApiTests(TestCase):
	"""
	Integration tests for the REST API endpoints (DRF layer).
	
	These tests validate the public API contract: the shape of responses,
	the serialization of nested data, and the behavior of custom actions.
	They protect the API that external clients or future frontend code will consume.
	"""

	def setUp(self) -> None:
		self.client = APIClient()

	def test_api_frontend_page_sets_csrf_cookie_and_loads_alpine(self) -> None:
		"""
		Validate that the API frontend page is usable for a browser fetch-based flow.

		How it works:
		1. Request the new frontend page.
		2. Assert that Django sets a CSRF cookie for the JavaScript fetch calls.
		3. Assert that the Alpine CDN script and the frontend bootstrap function are present.

		Why this matters:
		The frontend page is not a regular Django form page, so if the CSRF cookie is not
		set on first load, the vote request cannot succeed with SessionAuthentication.
		"""
		response = self.client.get(reverse("polls:api_frontend"))

		self.assertEqual(response.status_code, 200)
		self.assertIn("csrftoken", response.cookies)
		self.assertContains(response, "polls/api_frontend.css")
		self.assertContains(response, "polls/api_frontend.js")
		self.assertContains(response, "cdn.jsdelivr.net/npm/alpinejs")
		self.assertContains(response, "pollsFrontend")
		self.assertContains(response, "Audit log")
		self.assertContains(response, "User")
		self.assertContains(response, "Model")
		self.assertContains(response, "Event")
		self.assertContains(response, "Reset filters")
		self.assertContains(response, "Manage choices")
		self.assertContains(response, "Add a choice")
		self.assertContains(response, "Edit choice")
		self.assertContains(response, "Save choice")
		self.assertContains(response, "Delete")

	def test_api_question_detail_returns_nested_choices(self) -> None:
		"""
		Validate that GET /api/polls/<id>/ returns a question with nested choices.
		
		How it works:
		1. Create a Question and a Choice belonging to it.
		2. Send a GET request to the detail endpoint.
		3. Assert: status is 200, the response includes the question id and pub_date,
		   and the "choices" key contains the nested Choice data (id, choice_text, votes).
		
		Why this matters:
		The API detail view uses QuestionDetailSerializer, which includes a nested
		ChoiceSerializer for the "choices" field. This is the API contract that
		frontend code depends on. If someone changes the serializer or removes the
		prefetch_related(), this test will fail and alert us immediately.
		
		This guards against: serializer field removal, missing nested data, wrong field names.
		"""
		question = Question.objects.create(question_text="API question")
		choice = Choice.objects.create(question=question, choice_text="Choice A")

		response: Any = self.client.get(reverse("polls_api:question-detail", kwargs={"pk": question.pk}))

		# This guards the public API contract: detail responses must include nested choices.
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], question.pk)
		self.assertEqual(response.data["choice_count"], 1)
		self.assertEqual(response.data["choices"][0]["id"], choice.pk)
		self.assertEqual(response.data["choices"][0]["choice_text"], "Choice A")

	def test_api_question_list_returns_fresh_choice_count_after_new_choice(self) -> None:
		"""
		Validate that repeated list requests do not reuse stale annotated queryset results.

		Why this matters:
		The API frontend sidebar reads the question list endpoint. If DRF reuses a cached
		class-level queryset between requests, the sidebar can keep an old choice_count until
		the development server restarts.
		"""
		question = Question.objects.create(question_text="Fresh count API question")
		Choice.objects.create(question=question, choice_text="Choice A")

		first_response: Any = self.client.get(reverse("polls_api:question-list"))
		first_payload = next(item for item in first_response.data if item["id"] == question.pk)

		Choice.objects.create(question=question, choice_text="Choice B")

		second_response: Any = self.client.get(reverse("polls_api:question-list"))
		second_payload = next(item for item in second_response.data if item["id"] == question.pk)

		self.assertEqual(first_response.status_code, 200)
		self.assertEqual(second_response.status_code, 200)
		self.assertEqual(first_payload["choice_count"], 1)
		self.assertEqual(second_payload["choice_count"], 2)

	def test_api_add_choice_creates_choice_for_question(self) -> None:
		"""
		Validate that POST /api/polls/<id>/choices/ creates a new choice for the question.
		
		How it works:
		1. Create a Question.
		2. Send a POST request to the custom "add_choice" action with a JSON body.
		3. Assert: status is 201 (Created), the choice was saved to the database,
		   and the response includes the created choice with votes=0.
		
		Why this matters:
		This tests the custom @action endpoint and the ChoiceSerializer write behavior.
		It validates:
		- The custom action is routed correctly.
		- Input is parsed and validated by DRF (no missing-field errors here).
		- The choice is associated with the correct question.
		- read_only fields (id, votes) are set to their defaults.
		
		If someone removes the action, changes the serializer, or breaks the question
		association, this test fails immediately.
		"""
		question = Question.objects.create(question_text="API write question")
		csrf_client, csrf_token = build_authenticated_csrf_client("api-choice-creator")

		response: Any = csrf_client.post(
			reverse("polls_api:question-add-choice", kwargs={"pk": question.pk}),
			{"choice_text": "New option"},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Choice.objects.filter(question=question).count(), 1)
		self.assertEqual(response.data["choice_text"], "New option")
		self.assertEqual(response.data["votes"], 0)
		self.assertEqual(AuditLog.objects.count(), 1)
		audit_log = AuditLog.objects.get()
		self.assertEqual(audit_log.user, User.objects.get(username="api-choice-creator"))
		self.assertEqual(audit_log.model, "Choice")
		self.assertEqual(audit_log.event, "create")
		self.assertEqual(audit_log.object_id, str(response.data["id"]))
		self.assertIn('"choice_text": "New option"', audit_log.change_to)

	def test_api_add_choice_rejects_anonymous_user(self) -> None:
		"""
		Validate that POST /api/polls/<id>/choices/ rejects unauthenticated users.

		Why this matters:
		The login requirement now lives in DRF permissions instead of inline view logic,
		so we need one regression test that proves the permission gate still blocks
		anonymous writes before the serializer runs.
		"""
		question = Question.objects.create(question_text="Anonymous choice write question")

		response: Any = self.client.post(
			reverse("polls_api:question-add-choice", kwargs={"pk": question.pk}),
			{"choice_text": "Blocked option"},
			format="json",
		)

		self.assertEqual(response.status_code, 403)
		self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")
		self.assertEqual(Choice.objects.filter(question=question).count(), 0)
		self.assertEqual(AuditLog.objects.count(), 0)

	def test_api_add_choice_rejects_duplicate_choice_text(self) -> None:
		"""
		Validate that duplicate choice text is rejected for the same question.
		"""
		question = Question.objects.create(question_text="Duplicate choice question")
		Choice.objects.create(question=question, choice_text="Duplicate")
		csrf_client, csrf_token = build_authenticated_csrf_client("api-choice-duplicate")

		response: Any = csrf_client.post(
			reverse("polls_api:question-add-choice", kwargs={"pk": question.pk}),
			{"choice_text": "Duplicate"},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("choice_text", response.data)
		self.assertEqual(
			response.data["choice_text"][0],
			"A choice with this text already exists for this question.",
		)
		self.assertEqual(Choice.objects.filter(question=question, choice_text__iexact="Duplicate").count(), 1)
		self.assertEqual(AuditLog.objects.count(), 0)

	def test_api_audit_user_list_returns_distinct_usernames(self) -> None:
		"""
		Validate that the audit users endpoint returns the distinct actor usernames.

		How it works:
		1. Create two users and a question with a choice.
		2. Add audit log entries for both users.
		3. Request the audit users endpoint.
		4. Assert the response contains both usernames in a distinct list.

		Why this matters:
		The audit frontend uses this endpoint to populate the user filter autocomplete.
		If the endpoint returns duplicates or the wrong set of usernames, the filter
		will become noisy or incomplete and the audit search experience will suffer.
		"""
		user_one = User.objects.create_user(username="audit-user-one", password="secret123")
		user_two = User.objects.create_user(username="audit-user-two", password="secret123")
		question = Question.objects.create(question_text="Audit user endpoint question")
		Choice.objects.create(question=question, choice_text="Option A")

		AuditLog.objects.create(
			user=user_one,
			model="Choice",
			event="create",
			object_id="1",
			change_from="{}",
			change_to='{"choice_text": "Option A"}',
		)
		AuditLog.objects.create(
			user=user_two,
			model="UserVote",
			event="vote",
			object_id="2",
			change_from="{}",
			change_to='{"choice_id": 1}',
		)

		response: Any = self.client.get(reverse("polls_api:auditlog-users"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data, ["audit-user-one", "audit-user-two"])

	def test_api_update_choice_changes_choice_text(self) -> None:
		"""
		Validate that PATCH /api/polls/<id>/choices/<choice_id>/ updates a choice text.

		How it works:
		1. Create a question with one choice.
		2. Send a PATCH request through the API frontend session flow.
		3. Assert the response is 200 and the database record changes.

		Why this matters:
		This is the new round-2 write path. If routing, serializer write support, or
		question/choice matching breaks, the API frontend cannot support choice editing.
		"""
		question = Question.objects.create(question_text="API choice update question")
		choice = Choice.objects.create(question=question, choice_text="Old text")
		csrf_client, csrf_token = build_authenticated_csrf_client("api-choice-editor")

		response: Any = csrf_client.patch(
			reverse(
				"polls_api:question-update-choice",
				kwargs={"pk": question.pk, "choice_id": choice.pk},
			),
			{"choice_text": "Updated text"},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		choice.refresh_from_db()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["choice_text"], "Updated text")
		self.assertEqual(choice.choice_text, "Updated text")
		self.assertEqual(choice.votes, 0)
		self.assertEqual(AuditLog.objects.count(), 1)
		audit_log = AuditLog.objects.get()
		self.assertEqual(audit_log.user, User.objects.get(username="api-choice-editor"))
		self.assertEqual(audit_log.model, "Choice")
		self.assertEqual(audit_log.event, "update")
		self.assertEqual(audit_log.object_id, str(choice.pk))
		self.assertIn('"choice_text": "Old text"', audit_log.change_from)
		self.assertIn('"choice_text": "Updated text"', audit_log.change_to)

	def test_api_delete_choice_removes_choice_for_question(self) -> None:
		"""
		Validate that DELETE /api/polls/<id>/choices/<choice_id>/ removes the choice.

		How it works:
		1. Create a question with one choice.
		2. Send a DELETE request through the API frontend session flow.
		3. Assert the response is 204 and the database record is gone.

		Why this matters:
		The delete action is the last missing CRUD operation in the API frontend.
		If routing or the question-scoped lookup breaks, a choice could not be removed
		from the selected question.
		"""
		question = Question.objects.create(question_text="API choice delete question")
		choice = Choice.objects.create(question=question, choice_text="Temporary text")
		csrf_client, csrf_token = build_authenticated_csrf_client("api-choice-deleter")

		response: Any = csrf_client.delete(
			reverse(
				"polls_api:question-update-choice",
				kwargs={"pk": question.pk, "choice_id": choice.pk},
			),
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		self.assertEqual(response.status_code, 204)
		self.assertFalse(Choice.objects.filter(pk=choice.pk).exists())
		self.assertEqual(AuditLog.objects.count(), 1)
		audit_log = AuditLog.objects.get()
		self.assertEqual(audit_log.user, User.objects.get(username="api-choice-deleter"))
		self.assertEqual(audit_log.model, "Choice")
		self.assertEqual(audit_log.event, "delete")
		self.assertEqual(audit_log.object_id, str(choice.pk))
		self.assertIn('"choice_text": "Temporary text"', audit_log.change_from)
		self.assertIn('"deleted": true', audit_log.change_to)


class PollsApiVoteTests(TestCase):
	"""
	Integration tests for the vote-related API endpoints.

	These tests exercise the API vote action and ensure the public vote contract
	works for authenticated users, duplicate votes, anonymous access, and invalid choices.
	"""

	def setUp(self) -> None:
		self.client = APIClient()

	def test_api_vote_creates_user_vote_and_increments_choice_votes(self) -> None:
		"""
		Validate the new API vote endpoint end-to-end with session auth and CSRF.

		How it works:
		1. Log the user in with a real session.
		2. Load the API frontend page so Django sets the CSRF cookie.
		3. POST the vote through the API endpoint with the CSRF token in the header.
		4. Assert the response is 200 and the choice counter increases.

		Why this matters:
		This is the core Phase 7 write path. If session auth, CSRF, or the atomic vote
		update breaks, the API-driven frontend cannot be trusted.
		"""
		question = Question.objects.create(question_text="Vote API question")
		choice = Choice.objects.create(question=question, choice_text="Blue")
		user = User.objects.create_user(username="api-voter", password="secret123")
		csrf_client = APIClient(enforce_csrf_checks=True)
		csrf_client.force_login(user)
		csrf_client.get(reverse("polls:api_frontend"))
		csrf_token = csrf_client.cookies["csrftoken"].value

		response: Any = csrf_client.post(
			reverse("polls_api:question-vote", kwargs={"pk": question.pk}),
			{"choice": choice.pk},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		choice.refresh_from_db()

		self.assertEqual(response.status_code, 200)
		self.assertEqual(choice.votes, 1)
		self.assertEqual(UserVote.objects.count(), 1)
		self.assertEqual(response.data["choices"][0]["votes"], 1)
		self.assertEqual(response.data["user_choice_id"], choice.pk)
		self.assertEqual(AuditLog.objects.count(), 1)
		audit_log = AuditLog.objects.get()
		self.assertEqual(audit_log.user, user)
		self.assertEqual(audit_log.model, "UserVote")
		self.assertEqual(audit_log.event, "vote")
		self.assertEqual(audit_log.object_id, str(UserVote.objects.get().pk))
		self.assertIn('"choice_id": ', audit_log.change_to)

	def test_api_question_detail_includes_user_choice_id_for_authenticated_user(self) -> None:
		"""
		Validate that the question detail payload includes the authenticated user's selected choice.

		How it works:
		1. Create a question with two choices.
		2. Create a user and record a UserVote for the first choice.
		3. Authenticate as that user and request the question detail endpoint.
		4. Assert the response includes `user_choice_id` matching the selected choice.

		Why this matters:
		The API frontend depends on this field to show the user's selected vote and disable
		re-voting. Without it, the client would have to infer state incorrectly or make an
		extra request for the user's vote.
		"""
		question = Question.objects.create(question_text="Selected choice API question")
		first_choice = Choice.objects.create(question=question, choice_text="Blue")
		Choice.objects.create(question=question, choice_text="Green")
		user = User.objects.create_user(username="api-choice-selected", password="secret123")
		UserVote.objects.create(user=user, question=question, choice=first_choice)

		client = APIClient()
		client.force_login(user)
		response: Any = client.get(reverse("polls_api:question-detail", kwargs={"pk": question.pk}))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["user_choice_id"], first_choice.pk)

	def test_api_vote_rejects_duplicate_vote(self) -> None:
		"""
		Validate that the API vote endpoint keeps the one-vote-per-user rule intact.

		Why this matters:
		The new frontend uses the API directly, so the duplicate-vote guard must still be
		enforced there, not only in the old HTML form flow.
		"""
		question = Question.objects.create(question_text="Duplicate vote API question")
		first_choice = Choice.objects.create(question=question, choice_text="Blue")
		second_choice = Choice.objects.create(question=question, choice_text="Green")
		user = User.objects.create_user(username="api-double-voter", password="secret123")
		csrf_client = APIClient(enforce_csrf_checks=True)
		csrf_client.force_login(user)
		csrf_client.get(reverse("polls:api_frontend"))
		csrf_token = csrf_client.cookies["csrftoken"].value

		first_response: Any = csrf_client.post(
			reverse("polls_api:question-vote", kwargs={"pk": question.pk}),
			{"choice": first_choice.pk},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)
		second_response: Any = csrf_client.post(
			reverse("polls_api:question-vote", kwargs={"pk": question.pk}),
			{"choice": second_choice.pk},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		first_choice.refresh_from_db()
		second_choice.refresh_from_db()

		self.assertEqual(first_response.status_code, 200)
		self.assertEqual(second_response.status_code, 409)
		self.assertEqual(second_response.data["error_message"], "You already voted on this question.")
		self.assertEqual(first_choice.votes, 1)
		self.assertEqual(second_choice.votes, 0)
		self.assertEqual(UserVote.objects.count(), 1)
		self.assertEqual(AuditLog.objects.count(), 1)

	def test_api_vote_rejects_anonymous_user(self) -> None:
		"""
		Validate that the API vote endpoint rejects unauthenticated requests.
		
		How it works:
		1. Create a question and a choice.
		2. Submit a POST vote request without logging in.
		3. Assert: response is 403 (Forbidden), error message is shown, no vote is stored.
		
		Why this matters:
		The API is a separate public interface from the HTML form. It must also enforce
		authentication, or the one-user-one-vote rule becomes impossible to enforce.
		"""
		question = Question.objects.create(question_text="API auth question")
		choice = Choice.objects.create(question=question, choice_text="Blue")

		response: Any = self.client.post(
			reverse("polls_api:question-vote", kwargs={"pk": question.pk}),
			{"choice": choice.pk},
			format="json",
		)

		choice.refresh_from_db()

		self.assertEqual(response.status_code, 403)
		self.assertEqual(response.data["error_message"], "You must be logged in to vote.")
		self.assertEqual(UserVote.objects.count(), 0)
		self.assertEqual(choice.votes, 0)
		self.assertEqual(AuditLog.objects.count(), 0)

	def test_api_vote_rejects_invalid_choice(self) -> None:
		"""
		Validate that the API vote endpoint rejects choices from other questions.
		
		How it works:
		1. Create two separate Question objects, each with their own Choice.
		2. Log in a user.
		3. POST a vote request to Question 1, but with the choice_id from Question 2.
		4. Assert: response is 400 (Bad Request), error message is shown, votes unchanged.
		
		Why this matters:
		This guards the same boundary-checking logic as the HTML vote view.
		If the queryset filtering is removed or the choice validation is bypassed,
		a user could vote for a choice that doesn't belong to the question.
		"""
		question = Question.objects.create(question_text="Question one")
		other_question = Question.objects.create(question_text="Question two")
		other_choice = Choice.objects.create(question=other_question, choice_text="Mismatch")
		user = User.objects.create_user(username="api-boundary-check", password="secret123")
		csrf_client = APIClient(enforce_csrf_checks=True)
		csrf_client.force_login(user)
		csrf_client.get(reverse("polls:api_frontend"))
		csrf_token = csrf_client.cookies["csrftoken"].value

		response: Any = csrf_client.post(
			reverse("polls_api:question-vote", kwargs={"pk": question.pk}),
			{"choice": other_choice.pk},
			format="json",
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		other_choice.refresh_from_db()

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data["error_message"], "You didn't select a choice.")
		self.assertEqual(other_choice.votes, 0)
		self.assertEqual(UserVote.objects.count(), 0)
		self.assertEqual(AuditLog.objects.count(), 0)
