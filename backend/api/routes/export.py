import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.core.config import settings
from backend.workers.renderer.ffmpeg_engine import generate_proxy_worker

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
    Accepts the finalized client-approved blueprint adjustments, 
    and handles the production-ready rendering cuts.
    """
    if not payload.blueprint:
        raise HTTPException(status_code=400, detail="Cannot export video with an empty timeline blueprint.")

    if not os.path.exists(payload.original_video_path):
        raise HTTPException(status_code=404, detail="Source video file could not be found on the server.")

    # Convert the first valid active moment payload directly to dictionary arrays
    composition_data = {
        "original_video_path": payload.original_video_path,
        "blueprint": payload.blueprint[0].model_dump()
    }

    try:
        # Direct high-fidelity task thread invocation
        result = generate_proxy_worker.render_final_export(composition_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering Pipeline Fault: {str(e)}")
