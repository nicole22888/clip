import os
import uuid
import json
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from backend.core.config import settings
from backend.workers.inspector.vision_ai import analyze_video
from backend.workers.renderer.ffmpeg_engine import generate_proxy_worker

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

QUEUE_DIR = os.path.join(settings.BASE_DIR, "data", "queue")
RESULTS_DIR = os.path.join(QUEUE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_production_pipeline_bg(file_path: str, prompt: str, voice_text: str, voice_actor: str, result_file_path: str):
    try:
        logger.info("⚡ Gemini Cloud API pipeline ignited. Ingesting media timeline structures...")
        res_inspector = analyze_video.run(file_path, prompt)
        
        blueprint_data = res_inspector.get("analysis", [])
        
        rendering_payload = {
            "video_path": file_path,
            "blueprint": blueprint_data,
            "voice_text": voice_text,
            "voice_actor": voice_actor
        }
        
        logger.info(f"🎙️ Handing tracks to mixing engine with voice profile: {voice_actor}")
        res_renderer = generate_proxy_worker.generate_proxy(rendering_payload)
        
        with open(result_file_path, "w") as f:
            json.dump({"state": "SUCCESS", "result": res_renderer}, f)
        logger.info("✨ Production assembly line loops closed successfully!")
    except Exception as e:
        logger.error(f"❌ Production pipeline crash trace: {str(e)}")
        with open(result_file_path, "w") as f:
            json.dump({"state": "FAILURE", "error": str(e)}, f)

@router.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(None),
    prompt: str = Form("Find action highlights"),
    voice_text: str = Form("Watch this play!"),
    voice_actor: str = Form("en-US-ChristopherNeural")
):
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
            if os.path.exists(file_path): os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")
    else:
        sample_source = os.path.join(settings.BASE_DIR, "data/sample.mp4")
        if not os.path.exists(sample_source):
            raise HTTPException(status_code=400, detail="Drop a video at backend/data/sample.mp4 to run.")
        import shutil
        shutil.copy(sample_source, file_path)

    task_id = str(uuid.uuid4())
    result_file_path = os.path.join(RESULTS_DIR, f"{task_id}.json")

    with open(result_file_path, "w") as f:
        json.dump({"state": "STARTED"}, f)

    background_tasks.add_task(run_production_pipeline_bg, file_path, prompt, voice_text, voice_actor, result_file_path)

    return {"status": "queued", "task_id": task_id, "filename": unique_filename}

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
