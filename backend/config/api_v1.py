"""All /api/v1/ routes. Each app registers its read (and later /manage/) routes here."""

from django.conf import settings
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.intelligence.views import TelegramWebhookView
from core.views import api_not_found, health

urlpatterns = [
    path("health/", health, name="health"),
    path("academics/", include("apps.academics.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("timetable/imports/", include("apps.intelligence.timetable_urls")),
    path("timetable/", include("apps.timetable.urls")),
    path("sources/", include("apps.intelligence.urls")),
    path(
        "integrations/telegram/webhook/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
    ),
    # Staff area (each address checks the matching capability).
    path("manage/academics/", include("apps.academics.manage_urls")),
    path("manage/", include("apps.accounts.manage_urls")),
]

# OpenAPI schema + Swagger UI: development only (DEBUG=True).
if settings.DEBUG:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    ]

# Must stay LAST: unknown /api/v1/... paths return the JSON error format.
urlpatterns += [re_path(r"^.*$", api_not_found)]
