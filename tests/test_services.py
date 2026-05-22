"""
tests/test_services.py
───────────────────────
Unit tests for PDF extraction and Gemini response parsing.
Run with: pytest tests/ -v
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import EmptyPDFError, GeminiParseError, PDFTooLargeError
from app.schemas.resume import ResumeScoreResponse


# ════════════════════════════════════════════════════════════════════════════════
# PDF Service
# ════════════════════════════════════════════════════════════════════════════════

class TestExtractTextFromPDF:
    def test_raises_on_oversized_file(self):
        from app.services.pdf_service import extract_text_from_pdf

        oversized = b"x" * (11 * 1024 * 1024)  # 11 MB
        with pytest.raises(PDFTooLargeError):
            extract_text_from_pdf(oversized)

    def test_raises_on_empty_extraction(self):
        """A valid-looking PDF that yields no text should raise EmptyPDFError."""
        from app.services.pdf_service import extract_text_from_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("app.services.pdf_service.pdfplumber.open", return_value=mock_pdf):
            with pytest.raises(EmptyPDFError):
                extract_text_from_pdf(b"%PDF-fake-content")

    def test_extracts_text_successfully(self):
        from app.services.pdf_service import extract_text_from_pdf

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "John Doe\nSoftware Engineer"

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("app.services.pdf_service.pdfplumber.open", return_value=mock_pdf):
            text = extract_text_from_pdf(b"%PDF-fake-content")

        assert "John Doe" in text
        assert "Software Engineer" in text


# ════════════════════════════════════════════════════════════════════════════════
# Gemini Service — parsing logic
# ════════════════════════════════════════════════════════════════════════════════

class TestParseGeminiResponse:
    """Tests the private _parse_response helper directly."""

    def _parse(self, raw: str) -> ResumeScoreResponse:
        from app.services.gemini_service import _parse_response
        return _parse_response(raw)

    def test_parses_clean_json(self):
        payload = {
            "score": 82,
            "missing_skills": ["Kubernetes", "Terraform"],
            "recommended_project": "Build a CI/CD pipeline with GitHub Actions and Terraform.",
            "summary": "Strong Python background. Missing infra skills.",
        }
        result = self._parse(json.dumps(payload))
        assert result.score == 82
        assert "Kubernetes" in result.missing_skills

    def test_strips_markdown_fences(self):
        payload = {
            "score": 60,
            "missing_skills": ["Docker"],
            "recommended_project": "Containerise a Flask app.",
            "summary": "Decent match, needs containers.",
        }
        raw = f"```json\n{json.dumps(payload)}\n```"
        result = self._parse(raw)
        assert result.score == 60

    def test_raises_on_invalid_json(self):
        with pytest.raises(GeminiParseError):
            self._parse("This is not JSON at all.")

    def test_raises_on_missing_fields(self):
        # Missing 'recommended_project' and 'summary'
        raw = json.dumps({"score": 70, "missing_skills": ["Go"]})
        with pytest.raises(GeminiParseError):
            self._parse(raw)

    def test_score_out_of_range_raises(self):
        payload = {
            "score": 150,  # invalid
            "missing_skills": [],
            "recommended_project": "N/A",
            "summary": "Too high.",
        }
        with pytest.raises(Exception):  # pydantic ValidationError
            self._parse(json.dumps(payload))


# ════════════════════════════════════════════════════════════════════════════════
# Schema validation
# ════════════════════════════════════════════════════════════════════════════════

class TestResumeScoreResponse:
    def test_coerces_string_score(self):
        r = ResumeScoreResponse(
            score="75",  # type: ignore[arg-type]
            missing_skills=["FastAPI"],
            recommended_project="Build a REST API.",
            summary="Good match.",
        )
        assert r.score == 75

    def test_strips_empty_skills(self):
        r = ResumeScoreResponse(
            score=50,
            missing_skills=["  ", "Docker", ""],
            recommended_project="Something.",
            summary="OK.",
        )
        assert r.missing_skills == ["Docker"]