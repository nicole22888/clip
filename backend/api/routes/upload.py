import os
import uuid
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

# Absolute configuration paths
from backend.core.config import settings
from backend.workers.inspector.vision_ai import analyze_video
from backend.workers.choreographer.layout import calculate_layout
from backend.workers.tracker.motion import track_and_adjust
from backend.workers.renderer.ffmpeg_engine import generate_proxy

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

QUEUE_DIR = os.path.join(settings.BASE_DIR, "data", "queue")
RESULTS_DIR = os.path.join(QUEUE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_pipeline_in_background(file_path: str, prompt: str, result_file_path: str):
    """Executes the heavy AI download and processing tree without blocking network loops."""
    try:
        logger.info("Starting background AI pipeline execution (Model setup/inference)...")
        res_inspector = analyze_video.run(file_path, prompt)
        res_choreographer = calculate_layout.run(res_inspector)
        res_tracker = track_and_adjust.run(res_choreographer)
        res_renderer = generate_proxy.run(res_tracker)
        
        with open(result_file_path, "w") as f:
            json.dump({"state": "SUCCESS", "result": res_renderer}, f)
        logger.info("Background AI pipeline finished processing successfully!")
    except Exception as e:
        logger.error(f"Background pipeline execution failed: {str(e)}")
        with open(result_file_path, "w") as f:
            json.dump({"state": "FAILURE", "error": str(e)}, f)

@router.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(None),
    prompt: str = Form("Find the best action moments")
):
    """
    Production-safe background ingestion. Instantly returns a 200 OK status code 
    to stop frontend timeouts, processing the model assembly in the background.
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
            raise HTTPException(status_code=500, detail=f"Failed to save video chunk: {str(e)}")
    else:
        sample_source = os.path.join(settings.BASE_DIR, "data/sample.mp4")
        if not os.path.exists(sample_source):
            raise HTTPException(
                status_code=400, 
                detail="Proxy upload limit bypass active. Please drop a file at backend/data/sample.mp4 to continue."
            )
        import shutil
        shutil.copy(sample_source, file_path)

    task_id = str(uuid.uuid4())
    result_file_path = os.path.join(RESULTS_DIR, f"{task_id}.json")

    # Initialize a clean PENDING transaction state file record
    with open(result_file_path, "w") as f:
        json.dump({"state": "STARTED"}, f)

    # Offload the massive AI workflow download/run stack to the background threads immediately
    background_tasks.add_task(run_pipeline_in_background, file_path, prompt, result_file_path)

    # Return IMMEDIATELY within 5 milliseconds to satisfy the web browser request loop
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
