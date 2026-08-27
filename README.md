<div align="center">

# Summarizer‑HF

**An abstractive text summarization web app powered by a fine‑tuned T5 model, served through a FastAPI backend.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/🤗%20Transformers-T5-yellow)](https://huggingface.co/docs/transformers)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#license)

[Overview](#overview) • [Features](#features) • [Architecture](#architecture) • [Getting Started](#getting-started) • [API Reference](#api-reference) • [Roadmap](#roadmap)

</div>

## Overview

Summarizer‑HF is a full‑stack NLP application that turns long‑form text or documents into concise, readable summaries. It combines a fine‑tuned **T5** model with a lightweight **FastAPI** backend and a responsive vanilla‑JS frontend, so users can paste text or upload a file and get a summary — along with reduction statistics and estimated reading time saved — in seconds.

The project demonstrates an end‑to‑end machine learning product: model integration and inference, a typed REST API, file parsing for multiple document formats, and a polished, dependency‑free frontend.

## Features

- **Abstractive summarization** using a fine‑tuned T5 model (not just extractive sentence selection)
- **Multiple input methods** — paste text directly, or upload `.txt`, `.pdf`, or `.docx` files
- **Configurable summary length** — short, medium, and long presets
- **Robust input handling** — validation and configurable file‑size limits
- **Rich summary statistics**
  - Original and summary word counts
  - Character counts
  - Reduction percentage
  - Estimated reading time saved
- **Export options** — copy to clipboard or download as `.txt`
- **Polished UI** — responsive two‑pane layout with light and dark themes
- **Local session history** — up to 20 recent summaries, stored client‑side only
- **Production‑readiness basics** — health‑check endpoint reporting model status and device (CPU/GPU)

## Architecture

```
┌─────────────────┐      HTTP/JSON       ┌──────────────────────┐
│  Frontend (JS)   │ ───────────────────▶ │   FastAPI Backend    │
│  templates/      │ ◀─────────────────── │   app/main.py         │
│  static/         │                      └──────────┬───────────┘
└─────────────────┘                                  │
                                                       ▼
                                          ┌────────────────────────┐
                                          │  Extraction Layer       │
                                          │  app/extractors.py      │
                                          │  (TXT / PDF / DOCX)     │
                                          └────────────┬────────────┘
                                                       │
                                                       ▼
                                          ┌────────────────────────┐
                                          │  Inference Layer        │
                                          │  app/summarizer.py      │
                                          │  Fine‑tuned T5 (PyTorch)│
                                          └────────────────────────┘
```

**Tech stack**

| Layer | Technologies |
|---|---|
| Backend | FastAPI, Uvicorn, Pydantic |
| Machine Learning | PyTorch, Hugging Face Transformers, T5 |
| Frontend | HTML, CSS, vanilla JavaScript (no framework overhead) |
| Document parsing | PyPDF, python‑docx |

## Project Structure

```text
summarizer/
├── app/
│   ├── main.py          # FastAPI routes and application setup
│   ├── config.py        # Environment-based configuration
│   ├── schemas.py        # Request and response schemas
│   ├── summarizer.py    # T5 model loading and inference
│   └── extractors.py    # TXT, PDF, and DOCX text extraction
├── static/
│   ├── css/style.css    # Application styles
│   └── js/app.js        # Client-side interaction logic
├── templates/
│   └── index.html       # Main user interface
├── saved_summary_model/ # Local fine-tuned model files (not committed)
├── requirements.txt
├── .env.example
└── run.py
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- A saved T5 model and tokenizer, either:
  - in the local `saved_summary_model/` folder, or
  - hosted in a Hugging Face model repository

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/YOUR-USERNAME/summarizer-hf.git
   cd summarizer-hf
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   ```

   **Windows**
   ```bash
   venv\Scripts\activate
   ```

   **macOS/Linux**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your environment file**

   Windows:
   ```bash
   copy .env.example .env
   ```
   macOS/Linux:
   ```bash
   cp .env.example .env
   ```

5. **Configure the model path** in `.env`

   ```env
   SUMMARIZER_MODEL_NAME=./saved_summary_model
   ```

   Or point to a Hugging Face model repository:

   ```env
   SUMMARIZER_MODEL_NAME=your-username/your-model-name
   ```

6. **Start the application**

   ```bash
   python run.py
   ```

7. Open [http://localhost:8000](http://localhost:8000) in your browser.

## Configuration

All settings are configurable via environment variables.

| Variable | Default | Description |
|---|---:|---|
| `SUMMARIZER_MODEL_NAME` | `./saved_summary_model` | Local model path or Hugging Face model ID |
| `SUMMARIZER_MAX_INPUT_CHARS` | `20000` | Maximum characters accepted for summarization |
| `SUMMARIZER_MAX_UPLOAD_MB` | `10` | Maximum upload size in MB |

## API Reference

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "model": "./saved_summary_model",
  "device": "cpu"
}
```

`status` is `loading` while the model initializes and `ok` once it's ready — useful for readiness probes in a container or orchestration environment.

### Summarize Text

```http
POST /api/summarize
Content-Type: application/json
```

Request body:

```json
{
  "text": "Your text to summarize goes here.",
  "length": "medium"
}
```

Available values for `length`: `short`, `medium`, `long`

### Summarize a File

```http
POST /api/summarize-file
Content-Type: multipart/form-data
```

Form fields:

- `file` — a `.txt`, `.pdf`, or `.docx` file
- `length` — `short`, `medium`, or `long`

Example response:

```json
{
  "summary": "Generated summary text.",
  "original_word_count": 420,
  "summary_word_count": 75,
  "original_char_count": 2500,
  "summary_char_count": 460,
  "reduction_percent": 82.1,
  "estimated_reading_time_saved_sec": 104
}
```

## Notes

- The model loads once when the application starts, avoiding per‑request load latency.
- PDF extraction supports text‑based PDFs; scanned‑image PDFs require OCR, which is not currently implemented.
- Uploaded files are processed only to generate a summary; session history is stored client‑side in the browser and never persisted server‑side.
- The model directory is intentionally excluded from version control, since model‑weight files can exceed GitHub's file‑size limits. Store weights separately or publish them to a Hugging Face model repository.

