from django.conf import settings

from config.celery import app, ping


def test_celery_reads_the_django_settings():
    assert app.conf.broker_url == settings.CELERY_BROKER_URL
    assert app.conf.timezone == "Asia/Kuala_Lumpur"


def test_jobs_run_immediately_in_tests():
    # CELERY_TASK_ALWAYS_EAGER (test settings): no Redis or worker is needed.
    assert ping.delay().get() == "pong"
