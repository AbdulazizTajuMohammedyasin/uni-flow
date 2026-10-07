"""Tell Telegram where to send the bot's updates.

    pipenv run python manage.py set_telegram_webhook https://uniflow.example.com
    pipenv run python manage.py set_telegram_webhook --info
    pipenv run python manage.py set_telegram_webhook --delete

Needs TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET in backend/.env. Telegram only sends
to a public https address, so this is run where UniFlow is online (or through a tunnel).
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

from apps.intelligence import telegram


class Command(BaseCommand):
    help = "Set, show or remove the Telegram bot's webhook."

    def add_arguments(self, parser):
        parser.add_argument("site", nargs="?", help="UniFlow's public address (https://…).")
        parser.add_argument("--info", action="store_true", help="Show the current webhook.")
        parser.add_argument("--delete", action="store_true", help="Stop sending updates.")

    def handle(self, *args, site=None, info=False, delete=False, **options):
        try:
            if info:
                self.show_info()
            elif delete:
                telegram.call("deleteWebhook")
                self.stdout.write(self.style.SUCCESS("Telegram stopped sending updates."))
            else:
                self.set_webhook(site)
        except telegram.TelegramError as error:
            raise CommandError(str(error)) from error

    def set_webhook(self, site: str | None) -> None:
        if not site or not site.startswith("https://"):
            raise CommandError("Give UniFlow's public https address, e.g. https://uniflow.my")
        if not settings.TELEGRAM_WEBHOOK_SECRET:
            raise CommandError("Set TELEGRAM_WEBHOOK_SECRET in backend/.env first.")
        url = site.rstrip("/") + reverse("telegram-webhook")
        telegram.call(
            "setWebhook",
            url=url,
            secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
            allowed_updates=telegram.UPDATES,
        )
        self.stdout.write(self.style.SUCCESS(f"Telegram now sends the bot's updates to {url}"))

    def show_info(self) -> None:
        result = telegram.call("getWebhookInfo")
        self.stdout.write(f"Address: {result.get('url') or '(none)'}")
        self.stdout.write(f"Waiting to be sent: {result.get('pending_update_count', 0)}")
        if result.get("last_error_message"):
            self.stdout.write(self.style.WARNING(f"Last error: {result['last_error_message']}"))
