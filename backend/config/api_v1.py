"""All /api/v1/ routes. Each app registers its read (and later /manage/) routes here."""

from django.conf import settings
from django.urls import path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.views import api_not_found, health

urlpatterns = [
    path("health/", health, name="health"),
]

# OpenAPI schema + Swagger UI: development only (DEBUG=True).
if settings.DEBUG:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    ]

# Must stay LAST: unknown /api/v1/... paths return the JSON error format.
urlpatterns += [re_path(r"^.*$", api_not_found)]
