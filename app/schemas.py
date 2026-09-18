from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints


class SummarizeRequest(BaseModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50_000)
    ]
    language: Literal["Hindi", "Gujarati", "English"] = "Hindi"
    mode: Literal[
        "short", "detailed", "short_bullets", "long_bullets", "paragraph"
    ] = "short_bullets"


class SummarizeResponse(BaseModel):
    success: bool = True
    summary: str
    bulletPoints: list[str]
    detailedSummary: str
    serviceMode: str = "gemini"


class UsageCheckRequest(BaseModel):
    deviceId: str = Field(min_length=1)


class UsageIncrementRequest(BaseModel):
    deviceId: str = Field(min_length=1)


class UsageResetRequest(BaseModel):
    deviceId: str = Field(min_length=1)


class UsageResponse(BaseModel):
    success: bool = True
    deviceId: str
    used: int
    remainingFreeUses: int
    limit: int
    isPro: bool


class TranscribeResponse(BaseModel):
    success: bool = True
    uploadId: str
    filename: str
    language: str | None = None
    transcript: str = ""
    status: str = "not_configured"
    serviceMode: str = "gemini"
    message: str
