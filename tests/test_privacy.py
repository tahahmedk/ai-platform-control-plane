import logging

from fastapi.testclient import TestClient

from ai_platform.app import create_app
from ai_platform.config import load_settings
from ai_platform.providers import MockAdapter


def test_redacted_prompt_reaches_adapter_and_logs_exclude_content(caplog):
    seen = []

    class Capture(MockAdapter):
        async def complete(self, prompt, max_output_tokens):
            seen.append(prompt)
            return await super().complete(prompt, max_output_tokens)

    settings = load_settings()
    with caplog.at_level(logging.INFO, logger="ai_platform"):
        with TestClient(
            create_app(settings, {p.name: Capture() for p in settings.providers})
        ) as client:
            response = client.post(
                "/v1/infer",
                json={"tenant": "demo", "region": "us", "prompt": "Contact person@example.com"},
            )
    assert response.status_code == 200
    assert seen == ["Contact [EMAIL]"]
    assert "person@example.com" not in caplog.text
    assert "Contact" not in caplog.text


def test_unexpected_adapter_error_does_not_leak_or_retry(caplog):
    calls = []

    class Bug:
        async def complete(self, prompt, max_output_tokens):
            calls.append(prompt)
            raise RuntimeError("sensitive vendor payload")

    settings = load_settings()
    with TestClient(create_app(settings, {p.name: Bug() for p in settings.providers})) as client:
        response = client.post(
            "/v1/infer", json={"tenant": "demo", "region": "us", "prompt": "hello"}
        )
        assert response.status_code == 502
        assert client.get("/metrics").json()["errors"] == 1
    assert len(calls) == 1
    assert "sensitive vendor payload" not in response.text + caplog.text
