"""
app/services/groq_service.py
───────────────────────────
AI services using Groq for resume rewriting and cover letter generation.
Uses llama-3.3-70b-versatile — excellent quality, completely free.
"""

import json
from groq import Groq, APIError, APIConnectionError, RateLimitError

from app.core.config import get_settings
from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger
from app.schemas.resume import ResumeRewriteResponse, CoverLetterResponse

logger   = get_logger(__name__)
settings = get_settings()

_client = Groq(api_key=settings.groq_api_key)

# ─────────────────────────────────────────────────────────────────────────────
# RESUME REWRITING
# ─────────────────────────────────────────────────────────────────────────────

_REWRITE_SYSTEM_PROMPT = """\
You are an expert resume writer and career coach.

Your task is to rewrite a candidate's resume to better match a target job description.
Focus on highlighting relevant skills, experience, and accomplishments that align with the job.
Make the resume more compelling and ATS-friendly.

You MUST respond with ONLY a valid JSON object.
Do NOT use markdown. Do NOT use code fences. Do NOT write any text before or after the JSON.
Start your response with { and end it with }. Nothing else.

The JSON must conform exactly to this schema:
{
  "rewritten_resume": "<string>",
  "key_improvements": [<string>, ...],
  "summary": "<string>"
}

Field definitions:
- rewritten_resume: The improved resume text (keep formatting similar to original).
- key_improvements: Max 5 items. Specific improvements made (e.g., "Emphasized cloud architecture experience", "Added quantifiable metrics").
- summary: 2 sentences max. Overall improvement strategy applied.
"""

_REWRITE_USER_TEMPLATE = """\
## Original Resume
{resume_text}

---

## Target Job Description
{job_description}

Please rewrite the resume above to better match the job description. Highlight relevant skills and experience.
"""


def rewrite_resume(resume_text: str, job_description: str) -> ResumeRewriteResponse:
    """
    Rewrite a resume to match a job description using Groq.

    Raises
    ------
    GeminiAPIError   — API call failed
    GeminiParseError — response could not be parsed
    """
    user_message = _REWRITE_USER_TEMPLATE.format(
        resume_text=resume_text.strip(),
        job_description=job_description.strip(),
    )

    logger.info(
        "Sending rewrite request to Groq llama-3.3-70b (resume: %d chars, JD: %d chars)",
        len(resume_text), len(job_description),
    )

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _REWRITE_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
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
    return _parse_rewrite_response(raw_text)


# ─────────────────────────────────────────────────────────────────────────────
# COVER LETTER GENERATION
# ─────────────────────────────────────────────────────────────────────────────

_COVER_LETTER_SYSTEM_PROMPT = """\
You are an expert cover letter writer and career coach.

Your task is to write a compelling, professional cover letter that highlights the candidate's
strengths and explains why they are a perfect fit for the job.

You MUST respond with ONLY a valid JSON object.
Do NOT use markdown. Do NOT use code fences. Do NOT write any text before or after the JSON.
Start your response with { and end it with }. Nothing else.

The JSON must conform exactly to this schema:
{
  "cover_letter": "<string>",
  "key_highlights": [<string>, ...],
  "tone": "<string>"
}

Field definitions:
- cover_letter: The complete cover letter (3-4 paragraphs, professional tone).
- key_highlights: Max 4 items. Key strengths highlighted in the letter.
- tone: One word description of the tone (e.g., "professional", "enthusiastic", "strategic").
"""

_COVER_LETTER_USER_TEMPLATE = """\
## Candidate Resume
{resume_text}

---

## Target Job Description
{job_description}

Please write a professional cover letter for this candidate applying to this job.
Make it compelling, specific to the role, and highlight relevant experience and skills.
"""


def generate_cover_letter(resume_text: str, job_description: str) -> CoverLetterResponse:
    """
    Generate a cover letter using Groq.

    Raises
    ------
    GeminiAPIError   — API call failed
    GeminiParseError — response could not be parsed
    """
    user_message = _COVER_LETTER_USER_TEMPLATE.format(
        resume_text=resume_text.strip(),
        job_description=job_description.strip(),
    )

    logger.info(
        "Sending cover letter request to Groq llama-3.3-70b (resume: %d chars, JD: %d chars)",
        len(resume_text), len(job_description),
    )

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _COVER_LETTER_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
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
    return _parse_cover_letter_response(raw_text)


# ─────────────────────────────────────────────────────────────────────────────
# JSON PARSING
# ─────────────────────────────────────────────────────────────────────────────

def _parse_rewrite_response(raw: str) -> ResumeRewriteResponse:
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
        return ResumeRewriteResponse(**data)
    except Exception as exc:
        logger.error("Groq JSON failed schema validation: %s", data)
        raise GeminiParseError(
            f"AI response did not match expected schema: {exc}"
        ) from exc


def _parse_cover_letter_response(raw: str) -> CoverLetterResponse:
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
        return CoverLetterResponse(**data)
    except Exception as exc:
        logger.error("Groq JSON failed schema validation: %s", data)
        raise GeminiParseError(
            f"AI response did not match expected schema: {exc}"
        ) from exc
