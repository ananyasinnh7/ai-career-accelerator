"""
app/services/gemini_service.py
───────────────────────────────
Google Gemini integration using google-generativeai SDK.
"""

import json
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError

from app.core.config import get_settings
from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger
from app.schemas.resume import ResumeScoreResponse

logger   = get_logger(__name__)
settings = get_settings()

# ── Initialise SDK once at module load ─────────────────────────────────────────
genai.configure(api_key=settings.gemini_api_key)
_MODEL = genai.GenerativeModel(model_name=settings.gemini_model)

# ── Prompt ─────────────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are an expert technical recruiter and career coach.

Evaluate how well a candidate's resume matches a target job description.

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
- missing_skills: Max 8 items. Short phrases only (e.g. "Kubernetes", "unit testing").
- recommended_project: 2 sentences max. Include tech stack and a one-line pitch.
- summary: 2 sentences max. Key strengths and the single most important gap.
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
    Send resume + JD to Gemini and return a validated ResumeScoreResponse.

    Raises
    ------
    GeminiAPIError   — API call failed
    GeminiParseError — response could not be parsed into the schema
    """
    user_message = _USER_TEMPLATE.format(
        resume_text=resume_text.strip(),
        job_description=job_description.strip(),
    )

    logger.info(
        "Sending request to Gemini model '%s' (resume: %d chars, JD: %d chars)",
        settings.gemini_model, len(resume_text), len(job_description),
    )

    try:
        response = _MODEL.generate_content(
            contents=[
                {"role": "user", "parts": [_SYSTEM_PROMPT + "\n\n" + user_message]}
            ],
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=8192,
            ),
        )
    except GoogleAPICallError as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise GeminiAPIError(f"Gemini API error: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error calling Gemini")
        raise GeminiAPIError(f"Gemini API error: {exc}") from exc

    raw_text = _extract_text(response)
    logger.debug("Raw Gemini response: %s", raw_text[:500])
    return _parse_response(raw_text)


# ── Private helpers ────────────────────────────────────────────────────────────

def _extract_text(response) -> str:
    try:
        text = response.text
    except ValueError as exc:
        finish_reason = (
            response.candidates[0].finish_reason
            if response.candidates else "UNKNOWN"
        )
        raise GeminiAPIError(
            f"Gemini returned no content (finish_reason={finish_reason})."
        ) from exc

    if not text or not text.strip():
        raise GeminiAPIError("Gemini returned an empty response.")

    return text.strip()


def _parse_response(raw: str) -> ResumeScoreResponse:
    clean = raw.strip()

    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON. Raw: %s", raw[:300])
        raise GeminiParseError(
            f"Gemini response is not valid JSON: {exc}. Snippet: {raw[:200]}"
        ) from exc

    try:
        return ResumeScoreResponse(**data)
    except Exception as exc:
        logger.error("Gemini JSON failed schema validation: %s", data)
        raise GeminiParseError(
            f"Gemini response did not match expected schema: {exc}"
        ) from exc