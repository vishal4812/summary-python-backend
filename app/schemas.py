from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = "Hindi"
    mode: str = "short_bullets"


class SummarizeResponse(BaseModel):
    success: bool = True
    summary: str
    bulletPoints: list[str]
    detailedSummary: str
    serviceMode: str = "dummy"


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
    message: str
