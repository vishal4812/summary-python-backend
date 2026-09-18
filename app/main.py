from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import APP_NAME, APP_VERSION, FREE_LIMIT, MAX_AUDIO_UPLOAD_BYTES
from .schemas import (
    SummarizeRequest,
    SummarizeResponse,
    TranscribeResponse,
    UsageCheckRequest,
    UsageIncrementRequest,
    UsageResetRequest,
    UsageResponse,
)
from .services.summarizer import HeuristicSummarizer
from .services.transcriber import GeminiTranscriber, TranscriptionError
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
summarizer = HeuristicSummarizer()
transcriber = GeminiTranscriber()


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
    safe_name = Path(file.filename or "audio.bin").name
    try:
        contents = await file.read(MAX_AUDIO_UPLOAD_BYTES + 1)
        if not contents:
            raise HTTPException(status_code=422, detail="The audio file is empty.")
        if len(contents) > MAX_AUDIO_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Choose an audio file under 20 MB.")
        transcript = await transcriber.transcribe(
            filename=safe_name, contents=contents, language=language
        )
    except TranscriptionError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from None
    finally:
        await file.close()

    return TranscribeResponse(
        uploadId=uuid4().hex,
        filename=safe_name,
        language=language,
        transcript=transcript,
        status="completed",
        serviceMode="gemini",
        message="Audio transcribed successfully with Gemini.",
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
