from django.apps import AppConfig


class IntelligenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.intelligence"
    label = "intelligence"
    verbose_name = "Intelligence"

    def ready(self):
        from . import functions  # noqa: F401  (registers the Inngest functions)
