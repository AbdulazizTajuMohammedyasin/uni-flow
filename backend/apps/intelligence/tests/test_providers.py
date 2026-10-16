from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import CommandError, call_command
from google import genai
from google.genai import errors

from apps.intelligence.providers import (
    AIError,
    AIRateLimited,
    Attachment,
    FakeProvider,
    GeminiProvider,
    fake_provider,
    get_provider,
)

SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}}}


class FakeGoogleClient:
    """Stands in for google.genai.Client: returns `reply` or raises it."""

    def __init__(self, reply):
        self.reply = reply
        self.requests = []
        self.models = SimpleNamespace(generate_content=self.generate_content)

    def generate_content(self, **request):
        self.requests.append(request)
        if isinstance(self.reply, Exception):
            raise self.reply
        return SimpleNamespace(text=self.reply)


def gemini_with(monkeypatch, reply) -> tuple[GeminiProvider, FakeGoogleClient]:
    client = FakeGoogleClient(reply)

    def make_client(**options):
        client.options = options
        return client

    monkeypatch.setattr(genai, "Client", make_client)
    return GeminiProvider("test-key"), client


def ask(provider, **extra):
    return provider.ask_json(
        model="gemini-test", instructions="Be brief.", prompt="Hi", schema=SCHEMA, **extra
    )


def test_tests_always_use_the_fake_ai():
    assert get_provider() is fake_provider()


def test_the_fake_answers_in_order_and_records_questions():
    fake = FakeProvider(answers=[{"ok": True}, AIRateLimited("slow down")])
    assert ask(fake) == {"ok": True}
    with pytest.raises(AIRateLimited):
        ask(fake)
    with pytest.raises(AIError):
        ask(fake)  # nothing left
    assert [call["prompt"] for call in fake.calls] == ["Hi", "Hi", "Hi"]


def test_gemini_needs_a_key():
    with pytest.raises(AIError, match="GEMINI_API_KEY"):
        GeminiProvider("")


def test_gemini_tries_a_busy_model_again_after_a_few_seconds(monkeypatch):
    _, client = gemini_with(monkeypatch, '{"ok": true}')

    retry = client.options["http_options"].retry_options
    assert retry.attempts == 3 and retry.initial_delay == 2
    assert retry.http_status_codes == [500, 503]  # "too many requests" (429) is not retried


def test_gemini_asks_for_json_and_sends_files_first(monkeypatch):
    provider, client = gemini_with(monkeypatch, '{"ok": true}')

    answer = ask(provider, attachments=[Attachment(data=b"%PDF-1.7", mime_type="application/pdf")])

    assert answer == {"ok": True}
    [request] = client.requests
    assert request["model"] == "gemini-test"
    assert request["config"].response_mime_type == "application/json"
    assert request["config"].response_json_schema == SCHEMA
    assert request["config"].system_instruction == "Be brief."
    assert request["contents"][0].inline_data.mime_type == "application/pdf"
    assert request["contents"][-1] == "Hi"


def test_too_many_requests_becomes_rate_limited(monkeypatch):
    provider, _ = gemini_with(monkeypatch, errors.APIError(429, {"error": {"message": "quota"}}))
    with pytest.raises(AIRateLimited):
        ask(provider)


@pytest.mark.parametrize(
    "reply",
    [
        errors.APIError(500, {"error": {"message": "server"}}),
        ConnectionError("offline"),
        "not json",
    ],
)
def test_other_problems_become_ai_errors(monkeypatch, reply):
    provider, _ = gemini_with(monkeypatch, reply)
    with pytest.raises(AIError) as error:
        ask(provider)
    assert not isinstance(error.value, AIRateLimited)


def test_check_ai_command():
    fake_provider().answers.extend(
        [{"ok": True, "message": "fast ok"}, {"ok": True, "message": "smart ok"}]
    )
    output = StringIO()
    call_command("check_ai", stdout=output)
    assert "fast ok" in output.getvalue()
    assert "smart ok" in output.getvalue()

    with pytest.raises(CommandError, match="not working"):
        call_command("check_ai", stdout=StringIO())  # the fake has no answers left
