# UniFlow backend image: Django on gunicorn; background jobs run inside it too, called by Inngest.
# Built by deploy/docker-compose.yml (see docs/10-testing-and-deployment.md).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# mysqlclient needs the MySQL client library and a compiler to install.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Exactly the versions in Pipfile.lock, installed for the whole image (no virtualenv).
RUN pip install pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

COPY . .

# Run as a normal user, never root. /data/media holds uploaded files when no bucket is set.
RUN useradd --create-home uniflow \
    && mkdir -p /data/media /app/staticfiles \
    && chown -R uniflow /data /app/staticfiles
USER uniflow

# On every start: apply database changes and collect the admin's styles, then serve. (Render's
# free plan has no separate "before deploy" step, so the start does it.) Render gives the port
# in PORT; 8000 elsewhere. 2 workers fit the free 512 MB. --timeout 120: background jobs run
# inside requests from Inngest, and reading a timetable with the AI can take over 30 seconds.
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --access-logfile -"]
