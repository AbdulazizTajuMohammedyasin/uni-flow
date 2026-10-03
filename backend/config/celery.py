"""Celery: runs slow work (the AI, daily jobs) in the background, outside web requests.

Redis holds the to-do list (the "broker"). Start the worker from backend/:

    pipenv run celery -A config worker --pool=solo -l info   # --pool=solo: needed on Windows
    pipenv run celery -A config beat -l info                 # only for the daily jobs

Jobs are plain functions marked @shared_task in each app's tasks.py; Celery finds them
automatically. Settings starting with CELERY_ in config/settings configure it.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("uniflow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task
def ping() -> str:
    """A tiny job to check the set-up: `pipenv run celery -A config call config.celery.ping`
    and the worker's window shows "succeeded ... 'pong'"."""
    return "pong"
