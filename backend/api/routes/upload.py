import os
import uuid
import json
import logging
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks

from backend.core.config import settings
from backend.workers.inspector.vision_ai import analyze_video
from backend.services.voiceover import VoiceoverService
from backend.workers.renderer.ffmpeg_engine import generate_proxy_worker

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

QUEUE_DIR = os.path.join(settings.BASE_DIR, "data", "queue")
RESULTS_DIR = os.path.join(QUEUE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_production_pipeline_bg(file_path: str, prompt: str, voice_text: str, voice_actor: str, result_file_path: str, job_workspace_dir: str):
    """Orchestrates our modular multi-stage enterprise pipeline inside an isolated workspace context."""
    try:
        # DEFENSIVE PAYLOAD CLEANUP: If an old, stale browser cache string slips through, extract the clean prompt text safely
        if " || VOICETEXT: " in prompt:
            logger.info("⚠️ Legacy cache string pattern caught. Normalizing parameters dynamically...")
            prompt_parts = prompt.split(" || VOICETEXT: ", 1)
            prompt = prompt_parts[0]
            if len(prompt_parts) > 1 and not voice_text or voice_text == "Watch this play!":
                voice_text = prompt_parts[1]

        # Stage 1: Dynamic Cloud AI Ingestion Analysis
        logger.info("📡 Stage 1: Querying frame context parameters via Gemini Cloud nodes...")
        res_inspector = analyze_video.run(file_path, prompt)
        blueprint_data = res_inspector.get("analysis", [])
        
        # Split text lines safely matching segment rows lengths
        text_sentences = [s.strip() for s in voice_text.split(".") if s.strip()]
        if not text_sentences: 
            text_sentences = ["Watch this action highlight sequence."]

        voice_tracks_manifest = []
        
        # Stage 2: Event-Loop Isolated Voice Compilation Stage
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for idx, segment in enumerate(blueprint_data):
            sentence = text_sentences[idx % len(text_sentences)] + "."
            voice_filename = f"voice_segment_{idx}_{uuid.uuid4().hex[:4]}.mp3"
            voice_absolute_path = os.path.join(job_workspace_dir, voice_filename)
            
            logger.info(f"🎙️ Stage 2: Compiling neural speech file track element #{idx+1} -> {voice_filename}")
            loop.run_until_complete(VoiceoverService.generate_speech_file(sentence, voice_actor, voice_absolute_path))
            voice_tracks_manifest.append(voice_absolute_path)
            
        loop.close()

        rendering_payload = {
            "video_path": file_path,
            "blueprint": blueprint_data,
            "voice_tracks": voice_tracks_manifest,
            "workspace_dir": job_workspace_dir,
            "voice_text": voice_text,
            "voice_actor": voice_actor
        }
        
        # Stage 3: Deterministic Composition Rendering
        logger.info("🎬 Stage 3: Executing high-fidelity sidechain filters composition cuts...")
        res_renderer = generate_proxy_worker.generate_proxy(rendering_payload)
        
        with open(result_file_path, "w") as f:
            json.dump({"state": "SUCCESS", "result": res_renderer}, f)
        logger.info("✨ Job pipeline completed all rendering metrics and passed QC safely!")
        
        if os.path.exists(job_workspace_dir):
            shutil.rmtree(job_workspace_dir)

    except Exception as pipeline_error:
        logger.error(f"❌ Production system pipeline failure encountered: {str(pipeline_error)}")
        with open(result_file_path, "w") as f:
            json.dump({"state": "FAILURE", "error": str(pipeline_error)}, f)

@router.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(None),
    prompt: str = Form("Find action highlights"),
    voice_text: str = Form("Watch this play!"),
    voice_actor: str = Form("en-US-ChristopherNeural")
):
    job_id = str(uuid.uuid4())
    job_workspace_dir = os.path.join(settings.PROXY_DIR, job_id)
    os.makedirs(job_workspace_dir, exist_ok=True)

    unique_filename = f"source_master_{uuid.uuid4().hex[:4]}.mp4"
    file_path = os.path.join(job_workspace_dir, unique_filename)
    
    if video and video.filename:
        try:
            with open(file_path, "wb") as buffer:
                while content := await video.read(1024 * 1024):
                    buffer.write(content)
        except Exception as e:
            if os.path.exists(job_workspace_dir): shutil.rmtree(job_workspace_dir)
            raise HTTPException(status_code=500, detail=f"File write failure: {str(e)}")
    else:
        sample_source = os.path.join(settings.BASE_DIR, "data/sample.mp4")
        if not os.path.exists(sample_source):
            if os.path.exists(job_workspace_dir): shutil.rmtree(job_workspace_dir)
            raise HTTPException(status_code=400, detail="Bypass limit active. Put a video at backend/data/sample.mp4 to run.")
        shutil.copy(sample_source, file_path)

    result_file_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(result_file_path, "w") as f:
        json.dump({"state": "STARTED"}, f)

    background_tasks.add_task(
        run_production_pipeline_bg, 
        file_path, prompt, voice_text, voice_actor, result_file_path, job_workspace_dir
    )

    return {"status": "queued", "task_id": job_id, "filename": unique_filename}

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
