from django.contrib.auth import get_user_model
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse

from ..models import AuditLog, Choice, Question, UserVote

User = get_user_model()


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

		annotated_question = Question.objects.with_choice_count().get(pk=question.pk)

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
		self.assertEqual(AuditLog.objects.count(), 1)
		audit_log = AuditLog.objects.get()
		self.assertEqual(audit_log.user, user)
		self.assertEqual(audit_log.model, "UserVote")
		self.assertEqual(audit_log.event, "vote")
		self.assertEqual(audit_log.object_id, str(vote.pk))

	def test_vote_rejects_duplicate_vote(self) -> None:
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
		self.assertEqual(AuditLog.objects.count(), 1)

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
		self.assertEqual(AuditLog.objects.count(), 0)

	def test_vote_rejects_invalid_choice(self) -> None:
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
		self.assertEqual(AuditLog.objects.count(), 0)
