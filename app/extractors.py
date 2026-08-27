"""
Turns an uploaded .txt / .pdf / .docx file into plain text so it can be
fed to the summarizer. Isolated here so new formats are a one-function add.
"""
from io import BytesIO


class ExtractionError(ValueError):
    """Raised when a file's text can't be extracted (bad format, empty, etc.)."""


def extract_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "txt":
        return _extract_txt(content)
    if suffix == "pdf":
        return _extract_pdf(content)
    if suffix == "docx":
        return _extract_docx(content)
    raise ExtractionError(f"Unsupported file type: .{suffix}")


def _extract_txt(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="ignore")


def _extract_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError("PDF support requires the 'pypdf' package") from exc
    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc
    text = "\n".join(pages).strip()
    if not text:
        raise ExtractionError(
            "No extractable text found in this PDF (it may be a scanned image)."
        )
    return text


def _extract_docx(content: bytes) -> str:
    try:
        import docx
    except ImportError as exc:  # pragma: no cover
        raise ExtractionError("DOCX support requires the 'python-docx' package") from exc
    try:
        document = docx.Document(BytesIO(content))
        paragraphs = [p.text for p in document.paragraphs]
    except Exception as exc:
        raise ExtractionError(f"Could not read DOCX: {exc}") from exc
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ExtractionError("No text found in this document.")
    return text
