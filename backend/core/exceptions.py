"""One error format for the whole API (web and future mobile clients rely on it).

Every handled error response has the shape:

    {"error": {"code": "validation_error", "message": "...", "fields": {"title": ["..."]}}}

`fields` is always present; it is empty unless the error is a validation error.
"""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler

VALIDATION_MESSAGE = "Invalid input."


def api_exception_handler(exc, context):
    # Convert Django's exceptions to DRF ones first, so their code/message are known.
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:
        # Not an API error (a real bug): let Django produce its normal 500.
        return None

    if isinstance(exc, exceptions.ValidationError):
        detail = response.data
        fields = detail if isinstance(detail, dict) else {"non_field_errors": detail}
        error = {"code": "validation_error", "message": VALIDATION_MESSAGE, "fields": fields}
    else:
        codes = exc.get_codes() if isinstance(exc, exceptions.APIException) else None
        error = {
            "code": codes if isinstance(codes, str) else "error",
            "message": _message_from(response.data),
            "fields": {},
        }

    response.data = {"error": error}
    return response


def _message_from(data) -> str:
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    return str(data)
