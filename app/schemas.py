from typing import Literal

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw text to summarize.")
    length: Literal["short", "medium", "long"] = "medium"


class SummarizeResponse(BaseModel):
    summary: str
    original_word_count: int
    summary_word_count: int
    original_char_count: int
    summary_char_count: int
    reduction_percent: float
    estimated_reading_time_saved_sec: int


class HealthResponse(BaseModel):
    status: str
    model: str
    device: str
