"""Check that the AI key and models work: `pipenv run python manage.py check_ai`.

Asks every model of AI_FAST_MODELS and AI_SMART_MODELS one tiny question (one request from
each model's own free allowance) and says which ones answer, so the lists in .env can be
kept up to date when Google changes its models.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.intelligence.providers import AIBusy, AIError, AIRateLimited, get_provider

SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}, "message": {"type": "string"}},
    "required": ["ok", "message"],
}
INSTRUCTIONS = "You are a connection test. Answer only with the JSON asked for."
PROMPT = 'Reply with {"ok": true, "message": "UniFlow can reach the AI"}.'


class Command(BaseCommand):
    help = "Ask every configured AI model one tiny question, to check the key and models work."

    def handle(self, *args, **options):
        try:
            provider = get_provider()
        except AIError as error:
            raise CommandError(f"The AI is not working: {error}") from error
        working = 0
        for kind, models in [
            ("fast", settings.AI_FAST_MODELS),
            ("smart", settings.AI_SMART_MODELS),
        ]:
            for model in models:
                try:
                    answer = provider.ask_json(
                        model=model,
                        instructions=INSTRUCTIONS,
                        prompt=PROMPT,
                        schema=SCHEMA,
                    )
                except AIRateLimited:
                    self.stdout.write(self.style.WARNING(f"{kind} {model}: used up for today"))
                except AIBusy:
                    self.stdout.write(self.style.WARNING(f"{kind} {model}: busy, try later"))
                except AIError as error:
                    self.stdout.write(self.style.ERROR(f"{kind} {model}: {str(error)[:120]}"))
                else:
                    working += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"{kind} {model}: {answer.get('message')}")
                    )
        if working == 0:
            raise CommandError("The AI is not working: no model answered. Check GEMINI_API_KEY.")
