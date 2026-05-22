"""
app/services/pdf_service.py
────────────────────────────
Handles PDF ingestion: size validation + text extraction via pdfplumber.

Design notes
────────────
* Uses pdfplumber (superior table/layout handling over PyPDF2).
* Raises typed exceptions so the route layer can map them to HTTP codes.
* All I/O is synchronous; the FastAPI route runs this in a thread pool via
  `asyncio.to_thread` to keep the event loop unblocked.
"""

import io
import pdfplumber

from app.core.config import get_settings
from app.core.exceptions import EmptyPDFError, PDFExtractionError, PDFTooLargeError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract and return all text from a PDF supplied as raw bytes.

    Parameters
    ----------
    file_bytes:
        Raw PDF bytes read from the uploaded file.

    Returns
    -------
    str
        Concatenated text from all pages, stripped of excess whitespace.

    Raises
    ------
    PDFTooLargeError
        If the file exceeds ``settings.max_pdf_size_bytes``.
    PDFExtractionError
        If pdfplumber raises any unexpected error.
    EmptyPDFError
        If the extracted text is blank (e.g. a scanned/image-only PDF).
    """
    if len(file_bytes) > settings.max_pdf_size_bytes:
        max_mb = settings.max_pdf_size_bytes / (1024 * 1024)
        raise PDFTooLargeError(
            f"PDF size {len(file_bytes) / (1024*1024):.1f} MB exceeds the "
            f"{max_mb:.0f} MB limit."
        )

    logger.info("Extracting text from PDF (%d bytes)", len(file_bytes))

    try:
        pages_text: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            logger.debug("PDF has %d page(s)", len(pdf.pages))
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages_text.append(text)
                logger.debug("Page %d: %d chars extracted", i + 1, len(text))

        full_text = "\n\n".join(pages_text).strip()
    except (PDFTooLargeError, EmptyPDFError):
        raise
    except Exception as exc:
        logger.exception("pdfplumber failed to parse PDF")
        raise PDFExtractionError(f"Failed to parse PDF: {exc}") from exc

    if not full_text:
        raise EmptyPDFError(
            "No text could be extracted. The PDF may be image-only or encrypted. "
            "Please upload a text-based PDF."
        )

    logger.info("Extracted %d characters from PDF", len(full_text))
    return full_text
