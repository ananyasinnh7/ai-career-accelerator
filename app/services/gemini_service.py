"""
app/services/gemini_service.py
───────────────────────────────
Encapsulates all communication with the Google Gemini 3.0 API.

Design notes
────────────
* Uses ``google-generativeai`` SDK configured with the model string from settings.
* Prompts Gemini to return a strict JSON payload that maps 1-to-1 to
  ``ResumeScoreResponse``.
* Parses and validates the response with Pydantic — any schema mismatch raises
  ``GeminiParseError``, keeping the route layer clean.
* Runs synchronously; wrap with ``asyncio.to_thread`` in async routes.
"""

import json
import re

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError

from app.core.config import get_settings
from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger
from app.schemas.resume import ResumeScoreResponse

logger = get_logger(__name__)
settings = get_settings()

# ── Initialise Gemini SDK once at module load ──────────────────────────────────
genai.configure(api_key=settings.gemini_api_key)
_MODEL = genai.GenerativeModel(model_name=settings.gemini_model)

# ── Prompt template ────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are an expert technical recruiter and career coach with deep knowledge of \
software engineering, data science, product management, and related disciplines.

Your task is to evaluate how well a candidate's resume matches a target job description.

You MUST respond with ONLY a valid JSON object.
Do NOT use markdown. Do NOT use code fences. Do NOT write any text before or after the JSON.
Start your response with { and end it with }. Nothing else.

The JSON must conform exactly to this schema:

{
  "score": <integer 1-100>,
  "missing_skills": [<string>, ...],
  "recommended_project": "<string>",
  "summary": "<string>"
}

Field definitions:
- score: Overall match percentage (1 = no match, 100 = perfect match).
- missing_skills: List of specific skills, technologies, or competencies that \
  appear in the JD but are absent or insufficiently demonstrated in the resume. \
  Be precise (e.g. "Apache Kafka", not "messaging systems"). Max 10 items.
- recommended_project: A single, concrete, portfolio-ready project the candidate \
  should build to address the most critical skill gaps. Include the tech stack and \
  a one-sentence pitch for the project.
- summary: 2-3 sentences explaining the score, key strengths, and the single most \
  important gap to address.
"""
_USER_TEMPLATE = """\
## Candidate Resume
{resume_text}

---

## Target Job Description
{job_description}
"""


def score_resume(resume_text: str, job_description: str) -> ResumeScoreResponse:
    """
    Send resume + JD to Gemini and return a validated ``ResumeScoreResponse``.

    Parameters
    ----------
    resume_text:
        Plain text extracted from the candidate's PDF resume.
    job_description:
        The full text of the target job posting.

    Returns
    -------
    ResumeScoreResponse
        Validated structured evaluation from Gemini.

    Raises
    ------
    GeminiAPIError
        If the Gemini API call fails (network error, quota, auth, etc.).
    GeminiParseError
        If the response cannot be parsed or validated against the schema.
    """
    user_message = _USER_TEMPLATE.format(
        resume_text=resume_text.strip(),
        job_description=job_description.strip(),
    )

    logger.info(
        "Sending request to Gemini model '%s' (resume: %d chars, JD: %d chars)",
        settings.gemini_model,
        len(resume_text),
        len(job_description),
    )

    try:
        response = _MODEL.generate_content(
            contents=[
                {"role": "user", "parts": [_SYSTEM_PROMPT + "\n\n" + user_message]}
            ],
            generation_config=genai.GenerationConfig(
                temperature=0.2,          # low temp for deterministic scoring
                max_output_tokens=8192,
            ),
        )
    except GoogleAPICallError as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise GeminiAPIError(f"Gemini API error: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error calling Gemini")
        raise GeminiAPIError(f"Unexpected error: {exc}") from exc

    raw_text = _extract_text(response)
    logger.debug("Raw Gemini response: %s", raw_text[:500])

    return _parse_response(raw_text)


# ── Private helpers ────────────────────────────────────────────────────────────

def _extract_text(response: genai.types.GenerateContentResponse) -> str:
    """Pull the text out of the Gemini response, handling finish-reason edge cases."""
    try:
        text = response.text
    except ValueError as exc:
        # response.text raises ValueError when content is blocked
        finish_reason = (
            response.candidates[0].finish_reason
            if response.candidates
            else "UNKNOWN"
        )
        raise GeminiAPIError(
            f"Gemini returned no content (finish_reason={finish_reason}). "
            "The content may have been blocked."
        ) from exc

    if not text or not text.strip():
        raise GeminiAPIError("Gemini returned an empty response.")

    return text.strip()


def _parse_response(raw: str) -> ResumeScoreResponse:
    """Strip markdown fences and parse JSON into ResumeScoreResponse."""
    clean = raw.strip()

    # Remove ```json ... ``` or ``` ... ``` fences (multiline safe)
    if clean.startswith("```"):
        # Drop the opening fence line entirely
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean
        # Drop the closing fence
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON. Raw: %s", raw[:300])
        raise GeminiParseError(
            f"Gemini response is not valid JSON: {exc}. "
            f"Snippet: {raw[:200]}"
        ) from exc

    try:
        return ResumeScoreResponse(**data)
    except Exception as exc:
        logger.error("Gemini JSON failed schema validation: %s", data)
        raise GeminiParseError(
            f"Gemini response did not match expected schema: {exc}"
        ) from exc