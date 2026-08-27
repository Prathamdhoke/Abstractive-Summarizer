import logging

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.extractors import ExtractionError, extract_text
from app.schemas import HealthResponse, SummarizeRequest, SummarizeResponse
from app.summarizer import summarizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")

app = FastAPI(
    title="Text Summarizer",
    description="Abstractive text summarization powered by a fine-tuned T5 model.",
    version="2.0.0",
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def load_model_on_startup() -> None:
    # Loaded once, in a thread, so a slow first download doesn't block startup forever.
    await run_in_threadpool(summarizer.load)


def _build_response(original: str, summary: str) -> SummarizeResponse:
    original_words = len(original.split())
    summary_words = len(summary.split())
    reduction = 0.0 if original_words == 0 else round((1 - summary_words / original_words) * 100, 1)
    # Rough reading-time estimate at 200 words/minute.
    seconds_saved = max(0, round((original_words - summary_words) / 200 * 60))

    return SummarizeResponse(
        summary=summary,
        original_word_count=original_words,
        summary_word_count=summary_words,
        original_char_count=len(original),
        summary_char_count=len(summary),
        reduction_percent=reduction,
        estimated_reading_time_saved_sec=seconds_saved,
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok" if summarizer.is_ready else "loading",
        model=settings.MODEL_NAME,
        device=str(summarizer.device),
    )


@app.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_text(payload: SummarizeRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")
    if len(text) > settings.MAX_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Text exceeds the {settings.MAX_INPUT_CHARS}-character limit.",
        )

    preset = settings.LENGTH_PRESETS[payload.length]
    try:
        summary = await run_in_threadpool(
            summarizer.summarize, text, preset["min_length"], preset["max_length"]
        )
    except Exception as exc:
        logger.exception("Summarization failed")
        raise HTTPException(status_code=500, detail="Summarization failed. Please try again.") from exc

    return _build_response(text, summary)


@app.post("/api/summarize-file", response_model=SummarizeResponse)
async def summarize_file(file: UploadFile = File(...), length: str = Form("medium")):
    if length not in settings.LENGTH_PRESETS:
        raise HTTPException(status_code=400, detail="Invalid length preset.")

    suffix = "." + file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if suffix not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(settings.ALLOWED_UPLOAD_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB}MB limit.")

    try:
        text = extract_text(file.filename, content)
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    text = text[: settings.MAX_INPUT_CHARS]
    preset = settings.LENGTH_PRESETS[length]
    try:
        summary = await run_in_threadpool(
            summarizer.summarize, text, preset["min_length"], preset["max_length"]
        )
    except Exception as exc:
        logger.exception("Summarization failed")
        raise HTTPException(status_code=500, detail="Summarization failed. Please try again.") from exc

    return _build_response(text, summary)
