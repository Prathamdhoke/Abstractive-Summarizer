"""
Central configuration. Everything here can be overridden with an
SUMMARIZER_* environment variable (e.g. SUMMARIZER_MAX_INPUT_CHARS=5000)
so deployment doesn't require editing code.
"""
import os
from typing import Dict, Set


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Settings:
    # Path or HF hub id the model/tokenizer are loaded from.
    MODEL_NAME: str = os.getenv("SUMMARIZER_MODEL_NAME", "./saved_summary_model")

    # Guardrails for the API.
    MAX_INPUT_CHARS: int = _env_int("SUMMARIZER_MAX_INPUT_CHARS", 20_000)
    MAX_UPLOAD_MB: int = _env_int("SUMMARIZER_MAX_UPLOAD_MB", 10)
    ALLOWED_UPLOAD_EXTENSIONS: Set[str] = {".txt", ".pdf", ".docx"}

    # Generation presets exposed to the UI as Short / Medium / Long.
    LENGTH_PRESETS: Dict[str, Dict[str, int]] = {
        "short": {"min_length": 10, "max_length": 60},
        "medium": {"min_length": 40, "max_length": 150},
        "long": {"min_length": 100, "max_length": 300},
    }


settings = Settings()
