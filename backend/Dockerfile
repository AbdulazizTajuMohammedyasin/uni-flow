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

# Run as a normal user, never root. /data holds uploaded files and the scheduler's state.
RUN useradd --create-home uniflow \
    && mkdir -p /data/media /data/beat /app/staticfiles \
    && chown -R uniflow /data /app/staticfiles
USER uniflow

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
