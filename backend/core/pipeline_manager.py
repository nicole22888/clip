import os
from celery import Celery

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QUEUE_DIR = os.path.join(BASE_DIR, "data", "queue")
OUT_QUEUE = os.path.join(QUEUE_DIR, "out")
IN_QUEUE = os.path.join(QUEUE_DIR, "in")
RESULTS_DIR = os.path.join(QUEUE_DIR, "results")

# CRITICAL AUTOMATIC FIX: Securely create all worker directories on startup
for folder in [QUEUE_DIR, OUT_QUEUE, IN_QUEUE, RESULTS_DIR]:
    os.makedirs(folder, exist_ok=True)

# Define clean production filesystem pathways
FILESYSTEM_URL = "filesystem://"

celery_app = Celery(
    "video_pipeline",
    broker=FILESYSTEM_URL,
    backend=f"file://{RESULTS_DIR}",
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

# Production Grade Filesystem Transport Settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_track_started=True,
    result_expires=86400,
    
    # Configure the exact folder locations for message processing
    broker_transport_options={
        "data_folder_in": IN_QUEUE,
        "data_folder_out": OUT_QUEUE,
    }
)
