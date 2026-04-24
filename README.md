# Technical Assessment Spreash

Minimal Django 6 project with a Celery background task that creates a sample question every hour.

## Setup

```bash
uv sync
bash redis.sh
```

Then continue with Django:

```bash
cd djangotutorial
uv run python manage.py migrate
uv run python manage.py seed_polls
```

## Run

```bash
cd djangotutorial
uv run python manage.py runserver
uv run celery -A mysite worker -l info
uv run celery -A mysite beat -l info
```

## Redis

`redis.sh` is the default local helper. It starts `redis-broker` if the container already exists, or creates it with persistence if it does not.

For a quick temporary instance instead:

```bash
REDIS_MODE=quick bash redis.sh
```

## Test

```bash
uv run pytest
```

## Visit

The admin and (API-driven) frontend lives at:

```text
http://127.0.0.1:8000/admin/
http://127.0.0.1:8000/polls/
http://127.0.0.1:8000/polls/api-frontend/
```

If you want to vote there, log in first through the existing Django admin session at `/admin/`. The page reads questions from `/api/polls/`, loads a selected question from `/api/polls/<id>/`, and posts votes to `/api/polls/<id>/vote/`.

The classic tutorial pages remain available under `/polls/`, so you can compare the server-rendered flow with the API-driven version side by side.
