"""Check that the AI key and models work: `pipenv run python manage.py check_ai`."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.intelligence.providers import AIError, get_provider

SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}, "message": {"type": "string"}},
    "required": ["ok", "message"],
}


class Command(BaseCommand):
    help = "Ask the AI one tiny question with each model, to check the key and models work."

    def handle(self, *args, **options):
        try:
            provider = get_provider()
            for label, model in [
                ("fast", settings.AI_FAST_MODEL),
                ("smart", settings.AI_SMART_MODEL),
            ]:
                answer = provider.ask_json(
                    model=model,
                    instructions="You are a connection test. Answer only with the JSON asked for.",
                    prompt='Reply with {"ok": true, "message": "UniFlow can reach the AI"}.',
                    schema=SCHEMA,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"{label} model {model}: {answer.get('message')}")
                )
        except AIError as error:
            raise CommandError(f"The AI is not working: {error}") from error
