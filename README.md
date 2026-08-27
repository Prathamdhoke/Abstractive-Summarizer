# Summarizer-HF

Abstractive text summarization powered by a fine-tuned T5 model, served with
FastAPI. Paste text or drop in a `.txt` / `.pdf` / `.docx` file and get a
summary with word-count and reduction stats — history is kept client-side
only, in the browser.

## Project layout

```
summarizer/
├── app/
│   ├── main.py          # FastAPI routes, startup hook, response shaping
│   ├── config.py         # settings (env-var overridable)
│   ├── schemas.py        # request/response models
│   ├── summarizer.py     # model load + generation
│   └── extractors.py     # .txt/.pdf/.docx -> plain text
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
├── .env.example
└── run.py
```

## Setup

1. Place your fine-tuned model + tokenizer files where `SUMMARIZER_MODEL_NAME`
   points (defaults to `./saved_summary_model`, same as v1).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run it:
   ```bash
   python run.py
   # or: uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. Open `http://localhost:8000`.

## API

- `GET /health` → `{status, model, device}` — `status` is `"loading"` until
  the model finishes loading in the background at startup.
- `POST /api/summarize` → body `{text, length}` (`length` is
  `short` | `medium` | `long`), returns the summary plus word/char counts,
  reduction percentage, and estimated reading time saved.
- `POST /api/summarize-file` → multipart form with `file` and `length`,
  same response shape. Accepts `.txt`, `.pdf`, `.docx` up to
  `SUMMARIZER_MAX_UPLOAD_MB` (default 10MB).

Config knobs (`SUMMARIZER_MODEL_NAME`, `SUMMARIZER_MAX_INPUT_CHARS`,
`SUMMARIZER_MAX_UPLOAD_MB`) can be set via environment or a `.env` file —
see `.env.example`.

## What changed from v1

- Split the single `app.py` into a proper `app/` package (config, schemas,
  summarizer, extractors, routes) instead of one file mixing model loading,
  request handling, and templating.
- Model now loads once at startup in a background thread instead of at
  import time, and `/health` reports whether it's ready.
- Fixed a crash-on-CPU bug (`torch.cuda.is_availanle` typo) and added an
  `.eval()` + `torch.no_grad()` around generation.
- Added file upload (`.txt`/`.pdf`/`.docx`) alongside pasted text, with
  size/type validation.
- Length presets (short/medium/long) drive `min_length`/`max_length` instead
  of a single fixed length.
- New UI: word/char stats, a reduction-percent ring, copy/download actions,
  session history (stored in the browser only), and light/dark themes.
