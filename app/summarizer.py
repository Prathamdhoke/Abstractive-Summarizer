"""
Thin wrapper around the fine-tuned T5 model.

Kept separate from the API layer so `load()` can be called once at
startup (in a threadpool, so a slow first load doesn't block the event
loop) and so /health has something concrete to report on.
"""
import logging
import re
import threading

import torch
from transformers import AutoTokenizer, T5ForConditionalGeneration

from app.config import settings

logger = logging.getLogger("app.summarizer")


def _pick_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _clean(text: str) -> str:
    text = re.sub(r"\r\n", " ", text)   # normalize line endings
    text = re.sub(r"\s+", " ", text)    # collapse whitespace
    text = re.sub(r"<.*?>", " ", text)  # strip stray html tags
    return text.strip()


class Summarizer:
    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._device = _pick_device()
        self._lock = threading.Lock()

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def is_ready(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def load(self) -> None:
        """Idempotent — safe to call more than once (e.g. on retry)."""
        if self.is_ready:
            return
        with self._lock:
            if self.is_ready:
                return
            logger.info("Loading model '%s' onto %s", settings.MODEL_NAME, self._device)
            self._tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
            self._model = T5ForConditionalGeneration.from_pretrained(settings.MODEL_NAME)
            self._model.to(self._device)
            self._model.eval()
            logger.info("Model ready.")

    def summarize(self, text: str, min_length: int, max_length: int) -> str:
        if not self.is_ready:
            raise RuntimeError("Summarizer model is not loaded yet.")

        cleaned = _clean(text).lower()
        inputs = self._tokenizer(
            cleaned,
            padding="max_length",
            max_length=512,
            truncation=True,
            return_tensors="pt",
        ).to(self._device)

        with torch.no_grad():
            token_ids = self._model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                min_length=min_length,
                max_length=max_length,
                num_beams=4,
                early_stopping=True,
            )

        return self._tokenizer.decode(token_ids[0], skip_special_tokens=True)


summarizer = Summarizer()
