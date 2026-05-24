"""
app/services/cover_letter_generator.py
──────────────────────────────────────
Cover letter generation service using Groq LLM.
"""

import json
from groq import Groq

from app.core.config import get_settings
from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client = Groq(api_key=settings.groq_api_key)

_COVER_LETTER_SYSTEM_PROMPT = """\
You are an expert career coach specializing in persuasive, personalized cover letters.

Your task: Generate a compelling, non-generic cover letter that:
1. Opens with genuine interest in the specific role and company
2. Connects the candidate's experience to job requirements
3. Highlights key achievements with relevant numbers/impact
4. Shows cultural fit and enthusiasm
5. Closes with a clear call-to-action

The tone should be professional yet personable—not robotic.
The letter should be 3-4 short paragraphs.

You MUST respond with ONLY a valid JSON object.
Do NOT use markdown. Do NOT use code fences. Do NOT write any text before or after the JSON.

Response schema:
{
  "cover_letter": "<string with full cover letter>",
  "tone": "professional|enthusiastic|analytical"
}
"""

_COVER_LETTER_USER_TEMPLATE = """\
Candidate Information:
- Name: {candidate_name}
- Resume: {resume_text}

Target Position:
- Company: {company_name}
- Job Title: {job_title}
- Match Score: {match_score}/100

Job Description:
{job_description}

Generate a personalized cover letter for this candidate applying to this role.
"""


def generate_cover_letter(
    candidate_name: str,
    company_name: str,
    job_title: str,
    resume_text: str,
    job_description: str,
    match_score: int = 75,
) -> dict:
    """
    Generate a personalized cover letter.

    Args:
        candidate_name: Candidate's full name
        company_name: Target company name
        job_title: Target job title
        resume_text: Candidate's resume
        job_description: Job posting description
        match_score: AI match score for context (1-100)

    Returns:
        Dict with cover_letter and tone

    Raises:
        GeminiAPIError: API call failed
        GeminiParseError: Response parsing failed
    """
    user_message = _COVER_LETTER_USER_TEMPLATE.format(
        candidate_name=candidate_name,
        resume_text=resume_text.strip()[:2000],
        company_name=company_name,
        job_title=job_title,
        match_score=match_score,
        job_description=job_description.strip()[:2000],
    )

    logger.info(
        "Generating cover letter for %s at %s (%s)",
        candidate_name,
        company_name,
        job_title,
    )

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _COVER_LETTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=8192,
        )
    except Exception as exc:
        logger.error("Groq API error during cover letter generation: %s", exc)
        raise GeminiAPIError(f"Failed to generate cover letter: {exc}") from exc

    raw_text = response.choices[0].message.content or ""

    if not raw_text.strip():
        raise GeminiAPIError("Groq returned empty response during cover letter generation")

    logger.debug("Groq cover letter response: %s", raw_text[:300])

    try:
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]
            clean = clean.strip()

        data = json.loads(clean)
        return {
            "cover_letter": data.get("cover_letter", ""),
            "tone": data.get("tone", "professional"),
        }
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse cover letter JSON: %s", raw_text[:300])
        raise GeminiParseError(f"Invalid JSON response from AI: {exc}") from exc
