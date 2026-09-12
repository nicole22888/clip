import os
import uuid
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

# Absolute configuration path registers
from backend.core.config import settings
from backend.workers.inspector.vision_ai import analyze_video
from backend.workers.choreographer.layout import calculate_layout
from backend.workers.tracker.motion import track_and_adjust
# Aligned name matching the initialized class instance hook inside ffmpeg_engine.py
from backend.workers.renderer.ffmpeg_engine import generate_proxy_worker

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

QUEUE_DIR = os.path.join(settings.BASE_DIR, "data", "queue")
RESULTS_DIR = os.path.join(QUEUE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_production_pipeline_bg(file_path: str, prompt: str, result_file_path: str):
    """Executes the zero-cache cloud pipeline completely in an isolated thread context."""
    try:
        logger.info("⚡ Cloud API pipeline ignited. Contacting Gemini 3.8 Flash...")
        
        # Invoke worker scripts directly to drop old Celery socket cache maps
        res_inspector = analyze_video.run(file_path, prompt)
        res_choreographer = calculate_layout.run(res_inspector)
        res_tracker = track_and_adjust.run(res_choreographer)
        
        # Updated to leverage the proper production engine class method wrapper hook
        res_renderer = generate_proxy_worker.generate_proxy(res_tracker)
        
        with open(result_file_path, "w") as f:
            json.dump({"state": "SUCCESS", "result": res_renderer}, f)
        logger.info("✨ Cloud pipeline execution completed successfully!")
    except Exception as e:
        logger.error(f"❌ Cloud execution pipeline crash: {str(e)}")
        with open(result_file_path, "w") as f:
            json.dump({"state": "FAILURE", "error": str(e)}, f)

@router.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(None),
    prompt: str = Form("Find the best action moments")
):
    """
    Production Zero-Socket Ingestion. Completely circumvents old Celery connection 
    caches by processing workflows via clean local background threads.
    """
    unique_filename = f"{uuid.uuid4()}.mp4"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    if video and video.filename:
        _, file_extension = os.path.splitext(video.filename)
        if file_extension:
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
        try:
            with open(file_path, "wb") as buffer:
                while content := await video.read(1024 * 1024):
                    buffer.write(content)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")
    else:
        sample_source = os.path.join(settings.BASE_DIR, "data", "sample.mp4")
        if not os.path.exists(sample_source):
            raise HTTPException(
                status_code=400, 
                detail="Bypass upload limit active. Please drop a video at backend/data/sample.mp4 to run."
            )
        import shutil
        shutil.copy(sample_source, file_path)

    task_id = str(uuid.uuid4())
    result_file_path = os.path.join(RESULTS_DIR, f"{task_id}.json")

    with open(result_file_path, "w") as f:
        json.dump({"state": "STARTED"}, f)

    # Offload the cloud model assembly thread to background execution immediately
    background_tasks.add_task(run_production_pipeline_bg, file_path, prompt, result_file_path)

    return {
        "status": "queued", 
        "task_id": task_id,
        "filename": unique_filename
    }

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    result_file_path = os.path.join(RESULTS_DIR, f"{task_id}.json")
    if os.path.exists(result_file_path):
        try:
            with open(result_file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"task_id": task_id, "state": "PENDING"}
    return {"task_id": task_id, "state": "PENDING"}
