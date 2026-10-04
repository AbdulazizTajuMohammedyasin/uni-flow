"""The one place that talks to the AI (docs/12-intelligence.md, "AI provider").

The rest of the code asks for JSON that matches a schema and never imports a vendor
library. Two models are used:
- AI_FAST_MODEL: cheap and quick ("is this message academic?").
- AI_SMART_MODEL: understanding messages and reading timetable images, PDFs and sheets.

Providers: "gemini" (Google's Gemini API, key in GEMINI_API_KEY) and "fake" (tests).
When the AI says "too many requests", AIRateLimited is raised so the Celery job can wait
and retry later instead of failing.
"""

import json
from dataclasses import dataclass, field

from django.conf import settings


class AIError(Exception):
    """The AI could not answer (bad key, network, invalid reply...)."""


class AIRateLimited(AIError):
    """Too many requests for now (the free tier has per-minute and daily limits)."""


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
        )
        try:
            response = self._client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except errors.APIError as error:
            if error.code == 429:
                raise AIRateLimited(str(error)) from error
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
