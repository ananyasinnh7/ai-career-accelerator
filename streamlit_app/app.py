"""
streamlit_app/app.py
─────────────────────
MVP Streamlit frontend for the AI Career Accelerator.

Connects to the FastAPI backend at /api/v1/score-resume and presents
results in a clean, professional UI.
"""

import os
import time

import requests
import streamlit as st

# ── Page config (MUST be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="AI Career Accelerator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SCORE_ENDPOINT = f"{API_BASE_URL}/api/v1/score-resume"
REQUEST_TIMEOUT = 60  # seconds

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 50%, #0a0f1a 100%);
        min-height: 100vh;
    }

    /* ── Hero header ── */
    .hero-title {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 3.2rem;
        line-height: 1.1;
        background: linear-gradient(135deg, #e8e0ff 0%, #a78bfa 40%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }

    .hero-sub {
        font-family: 'DM Sans', sans-serif;
        font-weight: 300;
        font-size: 1.1rem;
        color: #94a3b8;
        letter-spacing: 0.01em;
        margin-bottom: 2.5rem;
    }

    /* ── Score card ── */
    .score-card {
        background: linear-gradient(135deg, rgba(167,139,250,0.15), rgba(56,189,248,0.08));
        border: 1px solid rgba(167,139,250,0.3);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }

    .score-number {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        font-size: 5rem;
        line-height: 1;
        background: linear-gradient(135deg, #a78bfa, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .score-label {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-weight: 500;
        margin-top: 0.25rem;
    }

    /* ── Section cards ── */
    .info-card {
        background: rgba(15, 15, 30, 0.8);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .card-title {
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #a78bfa;
        margin-bottom: 0.75rem;
    }

    .skill-chip {
        display: inline-block;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #fca5a5;
        border-radius: 50px;
        padding: 0.3rem 0.85rem;
        font-size: 0.82rem;
        margin: 0.2rem;
        font-weight: 500;
    }

    .project-box {
        background: rgba(56, 189, 248, 0.07);
        border-left: 3px solid #38bdf8;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.25rem;
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.65;
    }

    .summary-text {
        color: #cbd5e1;
        font-size: 0.95rem;
        line-height: 1.7;
        font-weight: 300;
    }

    /* ── Form styling ── */
    .upload-hint {
        font-size: 0.82rem;
        color: #475569;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }

    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.03em !important;
        transition: all 0.2s ease !important;
        margin-top: 0.5rem;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 30px rgba(124, 58, 237, 0.4) !important;
    }

    div[data-testid="stFileUploader"] {
        border: 1px dashed rgba(167,139,250,0.4) !important;
        border-radius: 12px !important;
        background: rgba(167,139,250,0.04) !important;
    }

    /* ── Divider ── */
    .section-divider {
        border: none;
        border-top: 1px solid rgba(99,102,241,0.15);
        margin: 2rem 0;
    }

    /* ── Score bar ── */
    .score-bar-track {
        background: rgba(255,255,255,0.06);
        border-radius: 100px;
        height: 8px;
        margin-top: 1rem;
        overflow: hidden;
    }

    .score-bar-fill {
        height: 100%;
        border-radius: 100px;
        background: linear-gradient(90deg, #a78bfa, #38bdf8);
        transition: width 1s ease;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helper functions ───────────────────────────────────────────────────────────

def score_color(score: int) -> str:
    if score >= 75:
        return "#4ade80"   # green
    if score >= 50:
        return "#fbbf24"   # amber
    return "#f87171"       # red


def render_score_gauge(score: int) -> str:
    color = score_color(score)
    label = (
        "Excellent Match" if score >= 75
        else "Partial Match" if score >= 50
        else "Low Match"
    )
    return f"""
    <div class="score-card">
        <div class="score-number" style="background: linear-gradient(135deg, {color}, #38bdf8);
             -webkit-background-clip: text; background-clip: text;">
            {score}
        </div>
        <div class="score-label">{label} · out of 100</div>
        <div class="score-bar-track">
            <div class="score-bar-fill" style="width:{score}%; background: linear-gradient(90deg, {color}, #38bdf8);"></div>
        </div>
    </div>
    """


def call_api(pdf_bytes: bytes, filename: str, job_description: str) -> dict:
    """POST to the FastAPI backend and return the parsed JSON response."""
    response = requests.post(
        SCORE_ENDPOINT,
        files={"resume": (filename, pdf_bytes, "application/pdf")},
        data={"job_description": job_description},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


# ── Main UI ────────────────────────────────────────────────────────────────────

def main() -> None:
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown('<div class="hero-title">AI Career Accelerator</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Upload your resume · paste a job description · get your match score & roadmap</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("#### 📄 Your Resume")
        uploaded_file = st.file_uploader(
            "Drop your PDF here",
            type=["pdf"],
            label_visibility="collapsed",
        )
        st.markdown('<p class="upload-hint">PDF only · Max 10 MB · Text-based (not scanned)</p>', unsafe_allow_html=True)

        st.markdown("#### 🎯 Target Job Description")
        job_description = st.text_area(
            "Paste the full job description",
            height=280,
            placeholder="Paste the complete job description here, including responsibilities, requirements, and preferred qualifications…",
            label_visibility="collapsed",
        )

        analyze_btn = st.button("✨ Analyse Match", use_container_width=True)

    with right_col:
        # ── Results panel ──────────────────────────────────────────────────────
        if "result" not in st.session_state:
            st.markdown(
                """
                <div style="
                    border: 1px dashed rgba(99,102,241,0.2);
                    border-radius: 20px;
                    padding: 4rem 2rem;
                    text-align: center;
                    color: #334155;
                ">
                    <div style="font-size:3rem;margin-bottom:1rem">🎯</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.1rem;color:#475569;font-weight:600;">
                        Your results will appear here
                    </div>
                    <div style="font-size:0.85rem;color:#334155;margin-top:0.5rem;">
                        Fill in the form and click Analyse Match
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            _render_results(st.session_state["result"])

    # ── Handle button click ───────────────────────────────────────────────────
    if analyze_btn:
        if not uploaded_file:
            st.error("Please upload a PDF resume.")
            return
        if not job_description or len(job_description.strip()) < 50:
            st.error("Please paste a job description (at least 50 characters).")
            return

        with st.spinner("Analysing your resume with Gemini AI…"):
            try:
                start = time.monotonic()
                result = call_api(
                    pdf_bytes=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    job_description=job_description,
                )
                elapsed = time.monotonic() - start

                st.session_state["result"] = result
                st.session_state["elapsed"] = round(elapsed, 1)
                st.rerun()

            except requests.exceptions.ConnectionError:
                st.error(
                    f"Cannot reach the API at `{API_BASE_URL}`. "
                    "Make sure the FastAPI server is running."
                )
            except requests.exceptions.Timeout:
                st.error("The request timed out. Try a shorter job description.")
            except requests.exceptions.HTTPError as exc:
                try:
                    detail = exc.response.json().get("detail", str(exc))
                except Exception:
                    detail = str(exc)
                st.error(f"API error: {detail}")


def _render_results(result: dict) -> None:
    """Render the structured analysis results."""
    score = result.get("score", 0)
    elapsed = st.session_state.get("elapsed", "?")

    # Score gauge
    st.markdown(render_score_gauge(score), unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align:center;color:#475569;font-size:0.78rem;margin-top:0.5rem;">'
        f'Analysis completed in {elapsed}s</p>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary
    summary = result.get("summary", "")
    if summary:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="card-title">💡 AI Summary</div>
                <div class="summary-text">{summary}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Missing skills
    missing = result.get("missing_skills", [])
    if missing:
        chips_html = "".join(f'<span class="skill-chip">⚡ {s}</span>' for s in missing)
        st.markdown(
            f"""
            <div class="info-card">
                <div class="card-title">🔴 Missing Skills</div>
                {chips_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Recommended project
    project = result.get("recommended_project", "")
    if project:
        st.markdown(
            f"""
            <div class="info-card">
                <div class="card-title">🛠️ Recommended Project</div>
                <div class="project-box">{project}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Reset button
    if st.button("🔄 Analyse Another Resume", use_container_width=True):
        del st.session_state["result"]
        st.rerun()


if __name__ == "__main__":
    main()