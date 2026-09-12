import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from celery import chain
from celery.result import AsyncResult

# Absolute layout path tracking alignments
from backend.core.config import settings
from backend.workers.inspector.vision_ai import analyze_video
from backend.workers.choreographer.layout import calculate_layout
from backend.workers.tracker.motion import track_and_adjust
from backend.workers.renderer.ffmpeg_engine import generate_proxy

router = APIRouter()

@router.post("/process")
async def process_video(
    video: UploadFile = File(...),
    prompt: str = Form("Find the best action moments")
):
    """Receives binary video stream chunks, locks them to raw upload data pools, and kicks off the factory pipeline."""
    # Robust file extension extraction tracking
    _, file_extension = os.path.splitext(video.filename)
    if not file_extension:
        file_extension = ".mp4"  # Safe delivery fallback mapping
        
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    try:
        # Stream the binary upload array cleanly down onto disk storage paths
        with open(file_path, "wb") as buffer:
            # Read in chunked blocks to protect virtual RAM footprints
            while content := await video.read(1024 * 1024):  # 1MB chunks
                buffer.write(content)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to securely save media stream: {str(e)}")
        
    # Fire the Assembly Line (Celery Chain Sequence)
    # Output arrays are passed forwards down the line automatically by the Redis broker engine
    workflow = chain(
        analyze_video.s(file_path, prompt),
        calculate_layout.s(),
        track_and_adjust.s(),
        generate_proxy.s()
    )
    
    task_chain = workflow.apply_async()
    
    return {
        "status": "queued", 
        "task_id": task_chain.id,
        "filename": unique_filename
    }

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    """Allows the mobile frontend application to poll the orchestration state engine."""
    res = AsyncResult(task_id)
    
    response_data = {
        "task_id": task_id,
        "state": res.state
    }
    
    if res.state == "SUCCESS":
        # When the proxy rendering finalizes, wrap up the metadata dictionaries cleanly
        response_data["result"] = res.result
    elif res.state == "FAILURE":
        response_data["error"] = str(res.info)
        
    return response_data
