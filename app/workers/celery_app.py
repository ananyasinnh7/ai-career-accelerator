"""
app/workers/celery_app.py
──────────────────────────
Celery application factory.

Setup:
1. Add to requirements.txt:
       celery==5.3.6
       redis==5.0.1

2. Add to .env:
       REDIS_URL=redis://localhost:6379/0

3. Run Redis (Docker):
       docker run -d -p 6379:6379 redis:7-alpine

4. Run Celery worker (separate terminal from your project root):
       celery -A app.workers.celery_app worker --loglevel=info

5. (Optional) Monitor jobs in browser at http://localhost:5555:
       celery -A app.workers.celery_app flower --port=5555
"""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ai_career_accelerator",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,        # keep results for 1 hour
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
