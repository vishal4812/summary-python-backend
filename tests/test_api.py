import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.main as main_module
from app.usage_store import UsageStore
from app.services.transcriber import GeminiTranscriber, TranscriptionError


@pytest.fixture(autouse=True)
def isolated_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "usage_store", UsageStore(tmp_path / "usage.db"))
    monkeypatch.setattr(main_module, "transcriber", GeminiTranscriber(api_key=""))


@pytest.fixture
def client():
    return TestClient(main_module.app)


def test_health_endpoint_returns_service_metadata(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "summary-app-backend",
        "version": "0.1.0",
    }


def test_summarize_returns_heuristic_summary_for_real_input(client):
    response = client.post(
        "/summarize",
        json={
            "text": (
                "The mobile app now supports uploading audio notes from the home screen. "
                "Users can track their free summary quota before upgrading to pro. "
                "The backend stores usage data in SQLite so local testing works offline. "
                "A cleaner summary response makes the app easier to demo to early users."
            ),
            "language": "English",
            "mode": "short_bullets",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["serviceMode"] == "heuristic"
    assert "uploading audio notes" in payload["summary"].lower()
    assert len(payload["bulletPoints"]) == 3
    assert all("dummy summary" not in point.lower() for point in payload["bulletPoints"])


def test_usage_endpoints_increment_and_reset_state(client):
    device_id = "device-123"

    check_response = client.post("/usage/check", json={"deviceId": device_id})
    increment_response = client.post("/usage/increment", json={"deviceId": device_id})
    reset_response = client.post("/usage/reset", json={"deviceId": device_id})

    assert check_response.status_code == 200
    assert check_response.json()["used"] == 0
    assert increment_response.status_code == 200
    assert increment_response.json()["used"] == 1
    assert reset_response.status_code == 200
    assert reset_response.json()["used"] == 0


def test_transcribe_returns_real_provider_result(client, monkeypatch):
    async def fake_transcribe(*, filename, contents, language):
        assert filename == "voice-note.wav"
        assert contents == b"wave-data"
        assert language == "Gujarati"
        return "કાલે સવારે મીટિંગ છે."

    monkeypatch.setattr(main_module.transcriber, "transcribe", fake_transcribe)
    response = client.post(
        "/transcribe",
        files={"file": ("voice-note.wav", b"wave-data", "audio/wav")},
        data={"language": "Gujarati"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["serviceMode"] == "gemini"
    assert payload["filename"] == "voice-note.wav"
    assert payload["transcript"] == "કાલે સવારે મીટિંગ છે."


@pytest.mark.parametrize(
    "filename,contents,language,status",
    [
        ("note.wav", b"", "English", 422),
        ("note.txt", b"text", "English", 415),
        ("note.wav", b"audio", "French", 422),
        ("note.wav", b"audio", "English", 503),
    ],
)
def test_transcribe_rejects_invalid_uploads_or_missing_key(
    client, filename, contents, language, status
):
    response = client.post(
        "/transcribe", files={"file": (filename, contents)}, data={"language": language}
    )
    assert response.status_code == status
    assert "transcript" not in response.json()


def test_transcribe_rejects_large_upload_before_provider_call(client, monkeypatch):
    monkeypatch.setattr(main_module, "MAX_AUDIO_UPLOAD_BYTES", 4)
    response = client.post("/transcribe", files={"file": ("note.wav", b"12345")})
    assert response.status_code == 413


def test_transcribe_preserves_provider_error_and_does_not_consume_usage(client, monkeypatch):
    async def fail(**kwargs):
        raise TranscriptionError("Gemini's usage limit was reached.", 429)

    monkeypatch.setattr(main_module.transcriber, "transcribe", fail)
    response = client.post("/transcribe", files={"file": ("note.wav", b"audio")})
    assert response.status_code == 429
    assert response.json()["detail"] == "Gemini's usage limit was reached."
    assert client.post("/usage/check", json={"deviceId": "test-device"}).json()["used"] == 0
