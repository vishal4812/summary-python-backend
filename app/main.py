from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import APP_NAME, APP_VERSION, FREE_LIMIT, UPLOADS_DIR
from .schemas import (
    SummarizeRequest,
    SummarizeResponse,
    TranscribeResponse,
    UsageCheckRequest,
    UsageIncrementRequest,
    UsageResetRequest,
    UsageResponse,
)
from .services.summarizer import DummySummarizer
from .usage_store import UsageStore

app = FastAPI(title=APP_NAME, version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

usage_store = UsageStore()
summarizer = DummySummarizer()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME, "version": APP_VERSION}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(payload: SummarizeRequest) -> SummarizeResponse:
    return summarizer.summarize(payload)


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
) -> TranscribeResponse:
    upload_id = uuid4().hex
    safe_name = Path(file.filename or "audio.bin").name
    destination = UPLOADS_DIR / f"{upload_id}_{safe_name}"
    contents = await file.read()
    destination.write_bytes(contents)
    language_label = language or "the selected language"
    transcript = (
        f"This is a placeholder transcript for {safe_name}. "
        f"The file upload reached the backend successfully in {language_label}, "
        "so the app and API are now integrated for the import flow. "
        "Real speech-to-text is not connected yet."
    )

    return TranscribeResponse(
      uploadId=upload_id,
      filename=safe_name,
      language=language,
      transcript=transcript,
      status="placeholder_transcript",
      message="Audio upload is working. Real transcription is not connected yet.",
    )


@app.post("/usage/check", response_model=UsageResponse)
def usage_check(payload: UsageCheckRequest) -> UsageResponse:
    record = usage_store.get_or_create(payload.deviceId)
    return UsageResponse(
        deviceId=record.device_id,
        used=record.used,
        remainingFreeUses=usage_store.remaining(record),
        limit=FREE_LIMIT,
        isPro=record.is_pro,
    )


@app.post("/usage/increment", response_model=UsageResponse)
def usage_increment(payload: UsageIncrementRequest) -> UsageResponse:
    record = usage_store.increment(payload.deviceId)
    return UsageResponse(
        deviceId=record.device_id,
        used=record.used,
        remainingFreeUses=usage_store.remaining(record),
        limit=FREE_LIMIT,
        isPro=record.is_pro,
    )


@app.post("/usage/reset", response_model=UsageResponse)
def usage_reset(payload: UsageResetRequest) -> UsageResponse:
    record = usage_store.reset(payload.deviceId)
    return UsageResponse(
        deviceId=record.device_id,
        used=record.used,
        remainingFreeUses=usage_store.remaining(record),
        limit=FREE_LIMIT,
        isPro=record.is_pro,
    )
