from django.test import TestCase
from unittest.mock import patch

from ..models import Choice, Question


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
	# 	
	# 	How it works:
	# 	1. Mock random.choice to return a predictable string.
	# 	2. Call create_smoke_question(), a faster-running variant for health checks.
	# 	3. Assert: Question was created and follows the expected naming pattern.
	# 	
	# 	Why this matters:
	# 	The smoke task runs every minute and is used to validate that Celery is alive.
	# 	If this breaks, you lose observability into whether the background system is running.
	# 	A failing task here alerts you immediately that the entire Celery infrastructure is down.
	# 	"""
	# 	from polls.tasks import create_smoke_question
	#
	# 	with patch('polls.tasks.random.choice', return_value='Smoke test question'):
	# 		question_pk = create_smoke_question()
	#
	# 	question = Question.objects.get(pk=question_pk)
	#
	# 	self.assertTrue(question.question_text.startswith('Smoke test question Celery phase '))
	# 	self.assertEqual(Choice.objects.filter(question=question).count(), 3)
