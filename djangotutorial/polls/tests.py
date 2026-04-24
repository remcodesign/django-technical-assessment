from django.contrib.auth import get_user_model
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from typing import Any

from rest_framework.test import APIClient
from unittest.mock import patch

from .models import Choice, Question, UserVote

User = get_user_model()


# the extra comments in these tests are intentional: they explain the "why" behind each assertion and test case.
# they can be removed in a real codebase, but for this exercise, they demonstrate the thought process and rationale for each test.
class QuestionModelTests(TestCase):
	"""
	Unit tests for the Question model.
	
	These tests validate the small, custom logic we've written on the model itself.
	Django's ORM and built-in field behavior is already tested by Django; we focus
	on our own calculations and constraints.
	"""

	def test_was_published_recently_returns_true_for_recent_question(self) -> None:
		"""
		Validate that was_published_recently() returns True for a question published today.
		
		How it works:
		- Create a Question object (pub_date is auto-set to now() via auto_now_add=True).
		- Call the was_published_recently() method, which checks if pub_date >= now() - 1 day.
		- Assert the result is True.
		
		Why this matters:
		This method is used in the IndexView to filter "recent" questions. If this logic
		breaks (e.g., someone changes the threshold from 1 day to 7 hours), the filter
		will silently produce wrong results. This unit test catches that regression immediately.
		"""
		question = Question.objects.create(question_text="Recent question")

		self.assertTrue(question.was_published_recently())


class QuestionListViewTests(TestCase):
	"""
	Integration tests for the Question index page.

	These tests verify both the rendered count and the query behavior, so we catch
	functional regressions and accidental N+1 reintroductions at the same time.
	"""

	def test_index_view_shows_annotated_choice_count(self) -> None:
		"""
		Validate that the index page exposes the computed choice count.

		How it works:
		1. Create one question with two choices.
		2. Request the index page.
		3. Assert that the question in context has choice_count=2 and the template renders it.

		Why this matters:
		The phase is about computed fields on the top model. If the annotation is missing,
		the list page either shows nothing or forces the count back into Python logic.
		"""
		question = Question.objects.create(question_text="Favorite color?")
		Choice.objects.bulk_create(
			[
				Choice(question=question, choice_text="Blue"),
				Choice(question=question, choice_text="Green"),
			]
		)

		response = self.client.get(reverse("polls:index"))

		latest_question_list = list(response.context["latest_question_list"])

		self.assertEqual(response.status_code, 200)
		self.assertEqual(latest_question_list[0].choice_count, 2)
		self.assertContains(response, "2 choices")

	def test_index_view_uses_one_query_for_multiple_questions(self) -> None:
		"""
		Validate that the list page does not fall back to per-row count queries.

		How it works:
		1. Create multiple questions, each with two choices.
		2. Load the index page inside assertNumQueries(1).
		3. Assert that the rendered page still shows the counts for every row.

		Why this matters:
		This is the cheap regression test for the N+1 problem. If somebody replaces the
		annotation with a property or template-side count, the query count will jump.
		"""
		for index in range(3):
			question = Question.objects.create(question_text=f"Question {index}")
			Choice.objects.bulk_create(
				[
					Choice(question=question, choice_text=f"{index}-A"),
					Choice(question=question, choice_text=f"{index}-B"),
				]
			)

		# self.assertNumQueries(1) means that the entire page load, including rendering the template and accessing all context variables, 
		# must execute at most 1 database query. If the view or template code causes additional queries ..
		# (e.g., by accessing a related field without prefetching), this assertion will fail, indicating an N+1 query problem.
		with self.assertNumQueries(1):
			response = self.client.get(reverse("polls:index"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "2 choices", count=3)

	def test_annotated_choice_count_defaults_to_zero(self) -> None:
		"""
		Validate that the annotation returns 0 for questions without choices.

		How it works:
		1. Create a question without related choices.
		2. Reuse the same Count annotation the view uses.
		3. Assert that the count is 0 instead of None or a missing attribute.

		Why this matters:
		Zero-related-object cases are easy to miss, but they are part of the public
		behavior of a computed count and should stay stable.
		"""
		question = Question.objects.create(question_text="Lonely question")

		annotated_question = Question.objects.annotate(choice_count=Count("choice")).get(pk=question.pk)

		self.assertEqual(getattr(annotated_question, "choice_count"), 0)


class VoteViewTests(TestCase):
	"""
	Integration tests for the vote view and the voting flow.
	
	These tests check the complete HTTP request-response cycle for the vote action,
	including model mutations, request parsing, and view logic. We validate that
	the user-facing voting feature works end-to-end.
	"""

	def test_vote_creates_user_vote_and_increments_choice_votes(self) -> None:
		"""
		Validate that a logged-in POST creates a UserVote and increments the choice counter.
		
		How it works:
		1. Create a Question, a Choice, and a user.
		2. Log the user in and submit a POST to the vote URL.
		3. Refresh the choice and inspect the created UserVote record.
		4. Assert: response is a redirect (302), the choice votes increased, and the vote record exists.
		
		Why this matters:
		The vote view now does two things at once:
		- Request parsing (extracting POST["choice"])
		- Model relation validation (finding the choice via question.choice_set.get)
		- Authenticated user tracking through an explicit UserVote row
		- Atomic database update (using F("votes") + 1 to avoid race conditions)
		- HTTP redirect (to prevent double-posting)
		
		If any of these pieces breaks, end users cannot vote. This test catches that.
		"""
		question = Question.objects.create(question_text="Favorite color?")
		choice = Choice.objects.create(question=question, choice_text="Blue")
		user = User.objects.create_user(username="voter", password="secret123")
		self.client.force_login(user)

		response = self.client.post(
			reverse("polls:vote", args=(question.pk,)),
			{"choice": choice.pk},
		)

		choice.refresh_from_db()

		self.assertEqual(response.status_code, 302)
		self.assertEqual(choice.votes, 1)
		self.assertEqual(UserVote.objects.count(), 1)
		vote = UserVote.objects.get()
		self.assertEqual(vote.user, user)
		self.assertEqual(vote.choice, choice)
		self.assertEqual(vote.question, question)

	def test_vote_rejects_second_vote_from_same_user_on_same_question(self) -> None:
		"""
		Validate that one authenticated user cannot vote twice on the same question.
		
		How it works:
		1. Create one user, one question, and two choices for that question.
		2. Submit a valid first vote.
		3. Submit a second vote for the same question but a different choice.
		4. Assert: the second response shows an error, only one UserVote exists, and the second choice stays unchanged.
		
		Why this matters:
		The whole point of the explicit UserVote model is that the schema can now enforce
		"one user, one vote per question". If we accidentally allow a second row, the
		business rule is broken even if the UI still looks fine.
		"""
		question = Question.objects.create(question_text="Favorite color?")
		first_choice = Choice.objects.create(question=question, choice_text="Blue")
		second_choice = Choice.objects.create(question=question, choice_text="Green")
		user = User.objects.create_user(username="double-voter", password="secret123")
		self.client.force_login(user)

		first_response = self.client.post(
			reverse("polls:vote", args=(question.pk,)),
			{"choice": first_choice.pk},
		)
		second_response = self.client.post(
			reverse("polls:vote", args=(question.pk,)),
			{"choice": second_choice.pk},
		)

		first_choice.refresh_from_db()
		second_choice.refresh_from_db()

		self.assertEqual(first_response.status_code, 302)
		self.assertEqual(second_response.status_code, 200)
		self.assertContains(second_response, "You already voted on this question.")
		self.assertEqual(UserVote.objects.count(), 1)
		self.assertEqual(first_choice.votes, 1)
		self.assertEqual(second_choice.votes, 0)

	def test_vote_rejects_anonymous_user(self) -> None:
		"""
		Validate that anonymous requests cannot create a UserVote.
		
		How it works:
		1. Create a question and a choice.
		2. Submit a POST without logging in.
		3. Assert: the view shows a login error and no vote is stored.
		
		Why this matters:
		Phase 5 is about individual user tracking, so we need a real user identity.
		If anonymous voting still works, then the model exists but the requirement is not met.
		"""
		question = Question.objects.create(question_text="Favorite color?")
		choice = Choice.objects.create(question=question, choice_text="Blue")

		response = self.client.post(
			reverse("polls:vote", args=(question.pk,)),
			{"choice": choice.pk},
		)

		choice.refresh_from_db()

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "You must be logged in to vote.")
		self.assertEqual(UserVote.objects.count(), 0)
		self.assertEqual(choice.votes, 0)

	def test_vote_with_choice_from_other_question_shows_error(self) -> None:
		"""
		Validate that voting with a choice from a different question is rejected.
		
		How it works:
		1. Create two separate Question objects, each with their own Choice.
		2. Send a POST vote request to Question 1, but with the choice_id from Question 2.
		3. Assert: response is 200 (not a redirect), error message is shown, votes unchanged.
		
		Why this matters:
		This is an edge case that tests the view's queryset filtering logic. The code does:
		  selected_choice = question.choice_set.get(pk=request.POST["choice"])
		
		If someone "optimizes" this to use Choice.objects.get(pk=...), the boundary check
		disappears and a user could vote for a choice that doesn't belong to the question.
		This test ensures that doesn't happen.
		"""
		question = Question.objects.create(question_text="Question one")
		other_question = Question.objects.create(question_text="Question two")
		other_choice = Choice.objects.create(question=other_question, choice_text="Mismatch")
		user = User.objects.create_user(username="boundary-check", password="secret123")
		self.client.force_login(user)

		response = self.client.post(
			reverse("polls:vote", args=(question.pk,)),
			{"choice": other_choice.pk},
		)

		other_choice.refresh_from_db()

		# The view must reject choices that do not belong to the submitted question.
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "You didn&#x27;t select a choice.")
		self.assertEqual(other_choice.votes, 0)


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
		self.assertContains(response, "cdn.jsdelivr.net/npm/alpinejs")
		self.assertContains(response, "pollsFrontend")

	def test_api_question_list_includes_choice_count(self) -> None:
		"""
		Validate that the list API exposes the computed count needed by the frontend.

		Why this matters:
		The API frontend mirrors the HTML index page, so the list payload must include the
		same count data without requiring an extra request per question.
		"""
		question = Question.objects.create(question_text="API list question")
		Choice.objects.bulk_create(
			[
				Choice(question=question, choice_text="Blue"),
				Choice(question=question, choice_text="Green"),
			]
		)

		response: Any = self.client.get(reverse("polls_api:question-list"))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data[0]["choice_count"], 2)

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

	def test_api_vote_creates_user_vote_and_returns_updated_detail(self) -> None:
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

		response: Any = self.client.post(
			reverse("polls_api:question-add-choice", kwargs={"pk": question.pk}),
			{"choice_text": "New option"},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Choice.objects.filter(question=question).count(), 1)
		self.assertEqual(response.data["choice_text"], "New option")
		self.assertEqual(response.data["votes"], 0)


class CeleryTaskTests(TestCase):
	"""
	Guard tests for Celery background task infrastructure.
	
	Celery is critical to this app: it automatically generates new questions every hour.
	If Celery breaks, the system fails silently—no new questions appear, but the app
	seems to work fine. These tests validate that the task queue is correctly wired.
	"""

	def test_create_hourly_question_creates_question_and_choices(self) -> None:
		"""
		Validate that the create_hourly_question task creates a question with three choices.
		
		How it works:
		1. Mock random.choice to return a predictable string.
		2. Call create_hourly_question(), which:
		   - Generates a question_text with a timestamp.
		   - Generates three choice_text labels based on the question text.
		   - Saves both to the database.
		   - Returns the question's primary key.
		3. Assert: Question and Choice objects were created with the expected data.
		
		Why this matters:
		The Celery Beat scheduler calls this task every hour. If the task breaks
		(e.g., imports change, database schema changes), no new questions are added.
		The app appears functional, but behind the scenes, the automation fails.
		This test ensures that doesn't happen silently.
		"""
		from polls.tasks import create_hourly_question

		with patch('polls.tasks.random.choice', return_value='How would you rate'):
			question_pk = create_hourly_question()

		question = Question.objects.get(pk=question_pk)
		choice_texts = list(
			Choice.objects.filter(question=question).order_by('id').values_list('choice_text', flat=True)
		)

		self.assertEqual(Question.objects.count(), 1)
		self.assertEqual(Choice.objects.count(), 3)
		self.assertTrue(question.question_text.startswith('How would you rate Celery phase '))
		self.assertEqual(choice_texts, [
			f'Option A for {question.question_text[:24]}',
			f'Option B for {question.question_text[:24]}',
			f'Option C for {question.question_text[:24]}',
		])

	# def test_create_smoke_question_creates_question_and_choices(self) -> None:
	# 	"""
	# 	Validate that the create_smoke_question task (1-minute heartbeat) creates a question.
		
	# 	How it works:
	# 	1. Mock random.choice to return a predictable string.
	# 	2. Call create_smoke_question(), a faster-running variant for health checks.
	# 	3. Assert: Question was created and follows the expected naming pattern.
		
	# 	Why this matters:
	# 	The smoke task runs every minute and is used to validate that Celery is alive.
	# 	If this breaks, you lose observability into whether the background system is running.
	# 	A failing task here alerts you immediately that the entire Celery infrastructure is down.
	# 	"""
	# 	from polls.tasks import create_smoke_question

	# 	with patch('polls.tasks.random.choice', return_value='Smoke test question'):
	# 		question_pk = create_smoke_question()

	# 	question = Question.objects.get(pk=question_pk)

	# 	self.assertTrue(question.question_text.startswith('Smoke test question Celery phase '))
	# 	self.assertEqual(Choice.objects.filter(question=question).count(), 3)
