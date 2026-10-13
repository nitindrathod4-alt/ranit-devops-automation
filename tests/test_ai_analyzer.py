
import json
from unittest.mock import patch

import pytest

from ranit.ai_analyzer import analyze_with_ai


def test_local_ai_uses_default_model(monkeypatch):
    monkeypatch.delenv("RANIT_AI_MODEL", raising=False)

    fake_response = {
        "message": {"content": "Check disk usage with df -h."}
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(fake_response).encode("utf-8")

    with patch(
        "ranit.ai_analyzer.urlopen",
        return_value=FakeResponse(),
    ) as mocked:
        answer = analyze_with_ai("No space left on device")

    assert answer == "Check disk usage with df -h."
    mocked.assert_called_once()

    request = mocked.call_args.args[0]
    assert request.full_url == "http://127.0.0.1:11434/api/chat"

    payload = json.loads(request.data.decode("utf-8"))
    assert payload["model"] == "qwen2.5:1.5b"
    assert payload["stream"] is False


def test_local_ai_uses_configured_model(monkeypatch):
    monkeypatch.setenv("RANIT_AI_MODEL", "qwen2.5-coder:0.5b")

    fake_response = {
        "message": {"content": "Inspect the preceding error."}
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(fake_response).encode("utf-8")

    with patch(
        "ranit.ai_analyzer.urlopen",
        return_value=FakeResponse(),
    ) as mocked:
        answer = analyze_with_ai("Build failed")

    assert answer == "Inspect the preceding error."

    payload = json.loads(
        mocked.call_args.args[0].data.decode("utf-8")
    )
    assert payload["model"] == "qwen2.5-coder:0.5b"


def test_local_ai_rejects_empty_model(monkeypatch):
    monkeypatch.setenv("RANIT_AI_MODEL", " ")

    with pytest.raises(ValueError, match="cannot be empty"):
        analyze_with_ai("Test log")


def test_local_ai_handles_connection_error():
    from urllib.error import URLError

    with patch(
        "ranit.ai_analyzer.urlopen",
        side_effect=URLError("connection refused"),
    ):
        with pytest.raises(RuntimeError, match="local Ollama"):
            analyze_with_ai("Test log")


def test_local_ai_handles_invalid_response():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"unexpected": "response"}'

    with patch(
        "ranit.ai_analyzer.urlopen",
        return_value=FakeResponse(),
    ):
        with pytest.raises(RuntimeError, match="valid answer"):
            analyze_with_ai("Test log")
