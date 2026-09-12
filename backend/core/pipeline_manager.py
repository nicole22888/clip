from celery import Celery
from core.config import settings

# Initialize the Factory Manager connecting to local Redis
celery_app = Celery(
    "video_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.workers.inspector.vision_ai",
        "backend.workers.choreographer.layout",
        "backend.workers.tracker.motion",
        "backend.workers.renderer.ffmpeg_engine"
    ] if "backend" in __name__ else [
        "workers.inspector.vision_ai",
        "workers.choreographer.layout",
        "workers.tracker.motion",
        "workers.renderer.ffmpeg_engine"
    ]
)

# Optimize for heavy video processing tasks
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1, # One heavy video task per worker at a time
    task_acks_late=True,          # Don't mark as complete until perfectly finished
    task_track_started=True,      # Let FastAPI track active video generation states
    result_expires=86400          # Clear cached task state details after 24 hours
)
