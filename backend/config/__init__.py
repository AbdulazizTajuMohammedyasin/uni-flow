# Load Celery when Django starts, so @shared_task jobs use this project's Celery app.
from .celery import app as celery_app

__all__ = ("celery_app",)
