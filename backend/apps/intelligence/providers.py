"""The one place that talks to the AI (docs/12-intelligence.md, "AI provider").

The rest of the code calls ask("fast" or "smart", ...) for JSON that matches a schema and
never imports a vendor library. Two kinds of model are used, each a list tried in order:
- AI_FAST_MODELS: cheap and quick ("is this message academic?").
- AI_SMART_MODELS: understanding messages and reading timetable images, PDFs and sheets.

On the free tier each model has its own small daily allowance. When a model says "too many
requests" (or is busy), it rests until Google says it can be used again, and the next model
in the list answers instead. Only when every model of the list is resting is AIRateLimited
raised, so the Celery job waits and retries later instead of failing.

Providers: "gemini" (Google's Gemini API, key in GEMINI_API_KEY) and "fake" (tests).
"""

import json
import re
from dataclasses import dataclass, field

from django.conf import settings
from django.core.cache import cache


class AIError(Exception):
    """The AI could not answer (bad key, network, invalid reply...)."""


class AIRateLimited(AIError):
    """Too many requests for now (the free tier has per-minute and daily limits)."""

    def __init__(self, message: str = "", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after  # seconds, when Google says


class AIBusy(AIError):
    """The model is overloaded right now ("high demand"); another one may answer."""


def _retry_after(message: str) -> int | None:
    """Google's "retryDelay": "49332s" in a 429 error, in seconds."""
    found = re.search(r"retryDelay['\"]?:\s*['\"](\d+)", message)
    return int(found.group(1)) if found else None


@dataclass
class Attachment:
    """A file sent with the question, e.g. a timetable image or PDF."""

    data: bytes
    mime_type: str


class GeminiProvider:
    def __init__(self, api_key: str):
        if not api_key:
            raise AIError("GEMINI_API_KEY is not set in backend/.env.")
        from google import genai  # imported here so tests never need the library or a key

        self._client = genai.Client(api_key=api_key)

    def ask_json(
        self,
        *,
        model: str,
        instructions: str,
        prompt: str,
        schema: dict,
        attachments: list[Attachment] | None = None,
    ) -> dict:
        from google.genai import errors, types

        contents: list = [
            types.Part.from_bytes(data=item.data, mime_type=item.mime_type)
            for item in attachments or []
        ]
        contents.append(prompt)
        config = types.GenerateContentConfig(
            system_instruction=instructions,
            response_mime_type="application/json",
            response_json_schema=schema,
            temperature=0,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        try:
            response = self._client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except errors.APIError as error:
            if error.code == 429:
                raise AIRateLimited(str(error), _retry_after(str(error))) from error
            if error.code in (500, 503):
                raise AIBusy(str(error)) from error
            raise AIError(str(error)) from error
        except Exception as error:  # network problems and the like
            raise AIError(str(error)) from error
        try:
            return json.loads(response.text or "")
        except json.JSONDecodeError as error:
            raise AIError("The AI did not answer with valid JSON.") from error


@dataclass
class FakeProvider:
    """For tests: answers come from `answers` in order, and every question is recorded."""

    answers: list = field(default_factory=list)
    calls: list = field(default_factory=list)

    def ask_json(self, **question) -> dict:
        self.calls.append(question)
        if not self.answers:
            raise AIError("The fake AI has no answer left.")
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


_fake = FakeProvider()


def get_provider():
    """The AI provider chosen by settings.AI_PROVIDER."""
    if settings.AI_PROVIDER == "fake":
        return _fake
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider(settings.GEMINI_API_KEY)
    raise AIError(f"Unknown AI_PROVIDER: {settings.AI_PROVIDER}")


def fake_provider() -> FakeProvider:
    """The shared fake (tests set its answers and read its calls)."""
    return _fake


# --- Asking, with fallback between models ---------------------------------------------------

MODEL_LISTS = {"fast": "AI_FAST_MODELS", "smart": "AI_SMART_MODELS"}
BUSY_REST = 60  # seconds a busy model rests
LIMIT_REST = 60  # when Google doesn't say how long


@dataclass
class Answer:
    data: dict
    model: str  # the model that answered (recorded on insights and timetable readings)


def _rest_key(model: str) -> str:
    return f"ai-resting:{model}"


def _record(kind: str, model: str, outcome: str, detail: str = "") -> None:
    """One row per request, for the operator's "AI requests" page (M9.4)."""
    from .models import AICall  # models import nothing from here; kept local for clarity

    AICall.objects.create(kind=kind, model=model, outcome=outcome, detail=detail[:300])


def ask(
    kind: str,
    *,
    instructions: str,
    prompt: str,
    schema: dict,
    attachments: list[Attachment] | None = None,
) -> Answer:
    """Ask the first model of the "fast" or "smart" list that isn't resting."""
    provider = get_provider()
    models = getattr(settings, MODEL_LISTS[kind])
    waits: list[int] = []
    for model in models:
        if cache.get(_rest_key(model)):
            continue
        try:
            data = provider.ask_json(
                model=model,
                instructions=instructions,
                prompt=prompt,
                schema=schema,
                attachments=attachments,
            )
        except AIRateLimited as error:  # its allowance is used up for now
            wait = error.retry_after or LIMIT_REST
            cache.set(_rest_key(model), True, timeout=wait)
            waits.append(wait)
            _record(kind, model, "used_up", f"resting {wait} s")
        except AIBusy as error:
            cache.set(_rest_key(model), True, timeout=BUSY_REST)
            waits.append(BUSY_REST)
            # Google's own words: tells "overloaded" apart from an error our request causes.
            _record(kind, model, "busy", str(error))
        except AIError as error:
            _record(kind, model, "failed", str(error))
            raise
        else:
            _record(kind, model, "answered")
            return Answer(data=data, model=model)
    raise AIRateLimited(
        f"Every {kind} model is used up or busy for now ({', '.join(models)}).",
        min(waits) if waits else LIMIT_REST,
    )
