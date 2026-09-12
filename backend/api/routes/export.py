import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from celery.result import AsyncResult

# Absolute layout path tracking alignments
from backend.core.config import settings
from backend.workers.renderer.ffmpeg_engine import render_final_export

router = APIRouter()

class MomentBlueprint(BaseModel):
    text: str
    start: float
    end: float
    x: float
    y: float
    style: str
    collision_detected: Optional[bool] = False

class ExportRequest(BaseModel):
    original_video_path: str
    blueprint: List[MomentBlueprint]

@router.post("/render")
async def trigger_export(payload: ExportRequest):
    """
    Accepts the finalized client-approved blueprint adjustments.
    Dispatches the high-quality 9:16 FFmpeg video render task.
    """
    if not payload.blueprint:
        raise HTTPException(status_code=400, detail="Cannot export video with an empty timeline blueprint.")

    if not os.path.exists(payload.original_video_path):
        raise HTTPException(status_code=404, detail="Source video file could not be found on the server.")

    # Convert Pydantic model array to primitive dict structure for Celery serialization
    composition_data = {
        "original_video_path": payload.original_video_path,
        "blueprint": [moment.model_dump() for moment in payload.blueprint]
    }

    # Dispatch to Worker 4's high-fidelity rendering pipeline
    task = render_final_export.delay(composition_data)

    return {
        "status": "rendering",
        "task_id": task.id
    }

@router.get("/status/{task_id}")
def get_export_status(task_id: str):
    """Tracks completion of high-resolution video generation tasks."""
    res = AsyncResult(task_id)
    
    response_data = {
        "task_id": task_id,
        "state": res.state
    }
    
    if res.state == "SUCCESS":
        response_data["status"] = "completed"
        response_data["download_url"] = f"/api/video/download/{res.result['export_filename']}"
    elif res.state == "FAILURE":
        response_data["status"] = "failed"
        response_data["error"] = str(res.info)
        
    return response_data
