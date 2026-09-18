import asyncio
import base64
import json

import httpx
import pytest

from app.services.transcriber import GeminiTranscriber, TranscriptionError


@pytest.mark.parametrize(
    "language,codes",
    [("Hindi", ["hi-IN", "en-IN"]), ("Gujarati", ["gu-IN", "en-IN"]),
     ("English", ["en-IN"]), (None, [])],
)
def test_gemini_request_and_transcript_extraction(language, codes):
    def respond(request):
        assert request.url.path == "/v1beta/interactions"
        assert not request.url.query
        assert request.headers["x-goog-api-key"] == "test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "gemini-3.5-transcribe"
        assert payload["store"] is False
        assert base64.b64decode(payload["input"][0]["data"]) == b"audio-bytes"
        assert payload["input"][0]["mime_type"] == "audio/m4a"
        assert payload["generation_config"]["transcription_config"]["language_codes"] == codes
        return httpx.Response(200, json={
            "status": "completed",
            "steps": [
                {"type": "thought", "content": [{"type": "text", "text": "Ignore this"}]},
                {"type": "model_output", "content": [
                    {"type": "text", "text": "  કાલે મીટિંગ છે.  "},
                    {"type": "text", "text": "Please join on time."},
                ]},
            ],
        })

    service = GeminiTranscriber(api_key="test-key", transport=httpx.MockTransport(respond))
    result = asyncio.run(service.transcribe(
        filename="note.M4A", contents=b"audio-bytes", language=language
    ))
    assert result == "કાલે મીટિંગ છે.\nPlease join on time."


@pytest.mark.parametrize("provider_status,expected_status", [
    (400, 422), (401, 503), (403, 503), (404, 503), (429, 429), (500, 502)
])
def test_provider_errors_do_not_expose_credentials(provider_status, expected_status):
    service = GeminiTranscriber(api_key="test-secret", transport=httpx.MockTransport(
        lambda request: httpx.Response(provider_status, json={"error": {"message": "test-secret"}})
    ))
    with pytest.raises(TranscriptionError) as error:
        asyncio.run(service.transcribe(filename="note.wav", contents=b"audio", language="English"))
    assert error.value.status_code == expected_status
    assert "test-secret" not in str(error.value)


@pytest.mark.parametrize("payload,status", [
    ({"status": "completed", "steps": []}, 422),
    ({"status": "failed"}, 502),
    ({"status": "completed", "steps": None}, 502),
    ([], 502),
])
def test_empty_or_invalid_transcripts_are_not_successful(payload, status):
    service = GeminiTranscriber(api_key="test-key", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload)
    ))
    with pytest.raises(TranscriptionError) as error:
        asyncio.run(service.transcribe(filename="note.wav", contents=b"audio", language=None))
    assert error.value.status_code == status


@pytest.mark.parametrize("failure,status", [
    (httpx.ReadTimeout, 504), (httpx.ConnectError, 502)
])
def test_network_failures_have_actionable_errors(failure, status):
    def respond(request):
        raise failure("test-secret", request=request)

    service = GeminiTranscriber(api_key="test-secret", transport=httpx.MockTransport(respond))
    with pytest.raises(TranscriptionError) as error:
        asyncio.run(service.transcribe(filename="note.wav", contents=b"audio", language=None))
    assert error.value.status_code == status
    assert "test-secret" not in str(error.value)
