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

`redis.sh` is the default local helper. It starts `redis-broker` if the container already exists, or creates it with persistence if it does not. `docker compose up -d` uses the same container name and a persistent volume.

For a quick temporary instance instead:

```bash
REDIS_MODE=quick bash redis.sh
```

## Test

```bash
uv run pytest
```