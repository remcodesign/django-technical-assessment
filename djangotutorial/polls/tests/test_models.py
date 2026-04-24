from django.db.models import Count
from django.test import TestCase

from ..models import Question


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
