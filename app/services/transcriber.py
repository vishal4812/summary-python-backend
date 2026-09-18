import base64
import os
from pathlib import Path

import httpx

AUDIO_MIME_TYPES = {
    ".aac": "audio/aac",
    ".m4a": "audio/m4a",
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
}
LANGUAGE_CODES = {
    "English": ["en-IN"],
    "Hindi": ["hi-IN", "en-IN"],
    "Gujarati": ["gu-IN", "en-IN"],
}


class TranscriptionError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class GeminiTranscriber:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = (
            api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        ).strip()
        self.model = model or os.getenv("GEMINI_STT_MODEL", "gemini-3.5-transcribe")
        self._transport = transport

    async def transcribe(
        self, *, filename: str, contents: bytes, language: str | None
    ) -> str:
        mime_type = AUDIO_MIME_TYPES.get(Path(filename).suffix.lower())
        if mime_type is None:
            raise TranscriptionError(
                "Choose an AAC, M4A, MP3, WAV, OGG, WebM, or FLAC audio file.", 415
            )
        if language is not None and language not in LANGUAGE_CODES:
            raise TranscriptionError("Choose Hindi, Gujarati, or English.", 422)
        if not self._api_key:
            raise TranscriptionError(
                "Audio transcription is not configured. Set GEMINI_API_KEY on the backend.",
                503,
            )

        payload = {
            "model": self.model,
            "input": [{
                "type": "audio",
                "data": base64.b64encode(contents).decode("ascii"),
                "mime_type": mime_type,
            }],
            "generation_config": {
                "transcription_config": {
                    "language_codes": LANGUAGE_CODES.get(language, []),
                    "mode": {"type": "verbatim"},
                }
            },
            "store": False,
        }
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(120, connect=15), transport=self._transport
            ) as client:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/interactions",
                    headers={"x-goog-api-key": self._api_key},
                    json=payload,
                )
        except httpx.TimeoutException:
            raise TranscriptionError(
                "Transcription timed out. Try a shorter audio file.", 504
            ) from None
        except httpx.RequestError:
            raise TranscriptionError(
                "Could not reach Gemini. Please try again.", 502
            ) from None

        if response.status_code == 429:
            raise TranscriptionError(
                "Gemini's usage limit was reached. Wait and try again, or check the backend project's quota.",
                429,
            )
        if response.status_code in (401, 403):
            raise TranscriptionError(
                "Gemini rejected the backend credentials. Check its API key and restrictions.",
                503,
            )
        if response.status_code == 404:
            raise TranscriptionError(
                "The configured Gemini transcription model is unavailable. Check GEMINI_STT_MODEL on the backend.",
                503,
            )
        if response.status_code in (400, 422):
            raise TranscriptionError(
                "Gemini could not process this audio. Try a different audio file.", 422
            )
        if not response.is_success:
            raise TranscriptionError("Gemini transcription failed. Please try again.", 502)

        try:
            result = response.json()
            if result.get("status") != "completed":
                raise ValueError("Incomplete transcription")
            parts = [
                part
                for step in result.get("steps", [])
                if step.get("type") == "model_output"
                for part in step.get("content", [])
            ]
            transcript = "\n".join(
                part["text"].strip()
                for part in parts
                if part.get("type") == "text" and isinstance(part.get("text"), str)
            ).strip()
        except (ValueError, TypeError, AttributeError, KeyError):
            raise TranscriptionError(
                "Gemini returned an invalid transcription response. Please try again.", 502
            ) from None
        if not transcript:
            raise TranscriptionError(
                "No speech was transcribed. Try an audio file with clear speech.", 422
            )
        return transcript
