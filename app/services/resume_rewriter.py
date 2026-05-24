"""
app/services/resume_rewriter.py
───────────────────────────────
Resume rewriting service using Groq LLM.
"""

import json
from groq import Groq

from app.core.config import get_settings
from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client = Groq(api_key=settings.groq_api_key)

_REWRITE_SYSTEM_PROMPT = """\
You are an expert career coach and resume writer.

Your task: Rewrite the candidate's resume bullet points to better align with a target job description.

IMPORTANT RULES:
1. Do NOT fabricate or lie about experience
2. Only reposition and reframe EXISTING skills and accomplishments
3. Use language and keywords from the job description
4. Make bullet points more impactful and quantifiable where possible
5. Maintain truthfulness and authenticity

You MUST respond with ONLY a valid JSON object.
Do NOT use markdown. Do NOT use code fences. Do NOT write any text before or after the JSON.

Response schema:
{
  "rewritten_resume": "<string with full rewritten resume>",
  "key_improvements": ["<improvement 1>", "<improvement 2>", ...]
}
"""

_REWRITE_USER_TEMPLATE = """\
## Target Job Description
{job_description}

---

## Candidate's Current Resume
{resume_text}

---

## Skills to Emphasize (Optional)
{missing_skills_context}

Rewrite the resume to better match the job description.
"""


def rewrite_resume(
    resume_text: str,
    job_description: str,
    missing_skills: list[str] | None = None,
) -> dict:
    """
    Rewrite resume bullets to align with job description.

    Args:
        resume_text: Original resume content
        job_description: Target job description
        missing_skills: Skills the candidate should emphasize

    Returns:
        Dict with rewritten_resume and key_improvements

    Raises:
        GeminiAPIError: API call failed
        GeminiParseError: Response parsing failed
    """
    missing_skills = missing_skills or []
    skills_context = (
        f"Try to demonstrate or highlight these areas: {', '.join(missing_skills)}"
        if missing_skills
        else "No specific skills to emphasize."
    )

    user_message = _REWRITE_USER_TEMPLATE.format(
        job_description=job_description.strip(),
        resume_text=resume_text.strip(),
        missing_skills_context=skills_context,
    )

    logger.info(
        "Rewriting resume (JD: %d chars, Resume: %d chars)",
        len(job_description),
        len(resume_text),
    )

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=8192,
        )
    except Exception as exc:
        logger.error("Groq API error during resume rewriting: %s", exc)
        raise GeminiAPIError(f"Failed to rewrite resume: {exc}") from exc

    raw_text = response.choices[0].message.content or ""

    if not raw_text.strip():
        raise GeminiAPIError("Groq returned empty response during resume rewriting")

    logger.debug("Groq rewrite response: %s", raw_text[:300])

    try:
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean
            if clean.endswith("```"):
                clean = clean.rsplit("```", 1)[0]
            clean = clean.strip()

        data = json.loads(clean)
        return {
            "rewritten_resume": data.get("rewritten_resume", ""),
            "key_improvements": data.get("key_improvements", []),
        }
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse resume rewrite JSON: %s", raw_text[:300])
        raise GeminiParseError(f"Invalid JSON response from AI: {exc}") from exc
