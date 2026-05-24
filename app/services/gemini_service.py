"""
app/services/gemini_service.py
───────────────────────────────
AI evaluation service using Groq (free tier).
Uses llama-3.3-70b-versatile — excellent quality, completely free.
"""

import json
from groq import Groq, APIError, APIConnectionError, RateLimitError

from app.core.config import get_settings
from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger
from app.schemas.resume import ResumeScoreResponse

logger   = get_logger(__name__)
settings = get_settings()

_client = Groq(api_key=settings.groq_api_key)

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
    Send resume + JD to Groq and return a validated ResumeScoreResponse.

    Raises
    ------
    GeminiAPIError   — API call failed
    GeminiParseError — response could not be parsed
    """
    user_message = _USER_TEMPLATE.format(
        resume_text=resume_text.strip(),
        job_description=job_description.strip(),
    )

    logger.info(
        "Sending request to Groq llama-3.3-70b (resume: %d chars, JD: %d chars)",
        len(resume_text), len(job_description),
    )

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.2,
            max_tokens=8192,
        )
    except RateLimitError as exc:
        logger.error("Groq rate limit: %s", exc)
        raise GeminiAPIError(f"AI rate limit exceeded: {exc}") from exc
    except APIConnectionError as exc:
        logger.error("Groq connection error: %s", exc)
        raise GeminiAPIError(f"AI connection error: {exc}") from exc
    except APIError as exc:
        logger.error("Groq API error: %s", exc)
        raise GeminiAPIError(f"AI service error: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error calling Groq")
        raise GeminiAPIError(f"Unexpected AI error: {exc}") from exc

    raw_text = response.choices[0].message.content or ""

    if not raw_text.strip():
        raise GeminiAPIError("Groq returned an empty response.")

    logger.debug("Raw Groq response: %s", raw_text[:500])
    return _parse_response(raw_text)


def _parse_response(raw: str) -> ResumeScoreResponse:
    """Strip optional markdown fences and parse JSON."""
    clean = raw.strip()

    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Groq JSON. Raw: %s", raw[:300])
        raise GeminiParseError(
            f"AI response is not valid JSON: {exc}. Snippet: {raw[:200]}"
        ) from exc

    try:
        return ResumeScoreResponse(**data)
    except Exception as exc:
        logger.error("Groq JSON failed schema validation: %s", data)
        raise GeminiParseError(
            f"AI response did not match expected schema: {exc}"
        ) from exc