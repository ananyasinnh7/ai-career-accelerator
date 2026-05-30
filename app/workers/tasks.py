"""
app/workers/tasks.py
─────────────────────
Celery background tasks.

The heavy Gemini scoring call runs here in a worker process,
not in the FastAPI request/response cycle.
"""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5, name="score_resume_task")
def score_resume_task(self, analysis_id: int):
    """
    Async resume scoring task.

    Called by POST /api/v1/score-resume/async
    Frontend polls GET /api/v1/score-resume/status/{analysis_id}
    until status == 'completed' or 'failed'.
    """
    try:
        from app.db.session import SessionLocal
        from app.db.models import ResumeAnalysis
        from app.services.gemini_service import score_resume

        db = SessionLocal()
        try:
            # Fetch the pending analysis record
            analysis = db.query(ResumeAnalysis).filter(
                ResumeAnalysis.id == analysis_id
            ).first()

            if not analysis:
                return {"error": "Analysis record not found"}

            # Mark as processing
            analysis.status = "processing"
            db.commit()

            # Run the Gemini scoring (the slow part — 3-5 seconds)
            result = score_resume(analysis.resume_text, analysis.job_description)

            # Save results
            analysis.score = result.score
            analysis.missing_skills = result.missing_skills
            analysis.recommended_project = result.recommended_project
            analysis.summary = result.summary
            analysis.status = "completed"
            db.commit()

            return {
                "analysis_id": analysis_id,
                "score": result.score,
                "status": "completed",
            }

        finally:
            db.close()

    except Exception as exc:
        # Retry up to 3 times on failure
        try:
            from app.db.session import SessionLocal
            from app.db.models import ResumeAnalysis
            db = SessionLocal()
            analysis = db.query(ResumeAnalysis).filter(
                ResumeAnalysis.id == analysis_id
            ).first()
            if analysis:
                analysis.status = "failed"
                db.commit()
            db.close()
        except Exception:
            pass

        raise self.retry(exc=exc)
