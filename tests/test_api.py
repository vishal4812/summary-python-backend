import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.main as main_module
from app.usage_store import UsageStore


@pytest.fixture(autouse=True)
def isolated_usage_store(tmp_path):
    original_uploads_dir = main_module.UPLOADS_DIR
    main_module.UPLOADS_DIR = tmp_path / "uploads"
    main_module.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    main_module.usage_store = UsageStore(tmp_path / "usage.db")
    yield
    main_module.UPLOADS_DIR = original_uploads_dir


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


def test_transcribe_accepts_uploads_and_marks_transcript_as_placeholder(client, tmp_path):
    audio_file = tmp_path / "voice-note.wav"
    audio_file.write_bytes(b"fake-wave-data")

    with audio_file.open("rb") as handle:
        response = client.post(
            "/transcribe",
            files={"file": ("voice-note.wav", handle, "audio/wav")},
            data={"language": "English"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "placeholder_transcript"
    assert payload["filename"] == "voice-note.wav"
    assert "upload is working" in payload["message"].lower()
