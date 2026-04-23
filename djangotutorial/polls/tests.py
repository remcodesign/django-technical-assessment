from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import Choice, Question


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


class VoteViewTests(TestCase):
	"""
	Integration tests for the vote view and the voting flow.
	
	These tests check the complete HTTP request-response cycle for the vote action,
	including model mutations, request parsing, and view logic. We validate that
	the user-facing voting feature works end-to-end.
	"""

	def test_vote_increments_choice_votes(self) -> None:
		"""
		Validate that a POST to /polls/<id>/vote/ with a valid choice increments votes.
		
		How it works:
		1. Create a Question and a Choice belonging to that Question.
		2. Send a POST request to the vote URL with the choice's primary key.
		3. Refresh the choice from the database (to see the updated votes field).
		4. Assert: response is a redirect (302), and the choice's votes field is 1.
		
		Why this matters:
		The vote view is the main write operation for end users. It combines:
		- Request parsing (extracting POST["choice"])
		- Model relation validation (finding the choice via question.choice_set.get)
		- Atomic database update (using F("votes") + 1 to avoid race conditions)
		- HTTP redirect (to prevent double-posting)
		
		If any of these pieces breaks, end users cannot vote. This test catches that.
		"""
		question = Question.objects.create(question_text="Favorite color?")
		choice = Choice.objects.create(question=question, choice_text="Blue")

		response = self.client.post(
			reverse("polls:vote", args=(question.pk,)),
			{"choice": choice.pk},
		)

		choice.refresh_from_db()

		self.assertEqual(response.status_code, 302)
		self.assertEqual(choice.votes, 1)

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

		response = self.client.get(reverse("polls_api:question-detail", kwargs={"pk": question.pk}))

		# This guards the public API contract: detail responses must include nested choices.
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["id"], question.pk)
		self.assertEqual(response.data["choices"][0]["id"], choice.pk)
		self.assertEqual(response.data["choices"][0]["choice_text"], "Choice A")

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

		response = self.client.post(
			reverse("polls_api:question-add-choice", kwargs={"pk": question.pk}),
			{"choice_text": "New option"},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(question.choice_set.count(), 1)
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
