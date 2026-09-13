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

# Extended Edge-TTS custom compiler that accepts dynamic formatting adjustments
async def compile_parameter_voiceover(text: str, voice: str, pitch_mod: str, rate_mod: str, target_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_mod, rate=rate_mod)
    await communicate.save(target_path)

def run_production_pipeline_bg(file_path: str, prompt: str, voice_text: str, voice_actor: str, result_file_path: str, job_workspace_dir: str):
    """Orchestrates our multi-stage autonomous screenwriter with an infinite voice-routing registry."""
    try:
        logger.info("📡 Stage 1: AI Screenwriter analyzing footage context and generating script...")
        res_inspector = analyze_video.run(file_path, prompt)
        blueprint_data = res_inspector.get("analysis", [])
        
        is_user_script_present = voice_text and voice_text != "Watch this play!"
        if is_user_script_present:
            import re
            user_phrases = [s.strip() for s in re.split(r'[.,\n]', voice_text) if s.strip()]
            normalized_blueprint = []
            for idx, item in enumerate(blueprint_data):
                phrase = user_phrases[idx % len(user_phrases)]
                normalized_blueprint.append({
                    "start": float(item["start"]),
                    "end": float(item["end"]),
                    "character_persona": item.get("character_persona", "Narrator"),
                    "vocal_delivery": item.get("vocal_delivery", "normal"),
                    "audio_fx": item.get("audio_fx", "clean_studio"),
                    "text": phrase
                })
        else:
            normalized_blueprint = blueprint_data

        GLOBAL_VOICE_POOL = [
            voice_actor, "en-US-EmmaNeural", "en-US-AndrewNeural", 
            "en-GB-RyanNeural", "en-US-AvaNeural", "en-US-BrianNeural"
        ]

        persona_voice_registry = {}
        allocated_voice_index = 0
        voice_tracks_manifest = []
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        for idx, segment in enumerate(normalized_blueprint):
            current_line = str(segment["text"])
            raw_persona_name = str(segment.get("character_persona", "Narrator")).strip()
            delivery = str(segment.get("vocal_delivery", "normal")).strip()
            
            # Map Persona names to specific actors
            if raw_persona_name not in list(persona_voice_registry.keys()):
                target_actor = GLOBAL_VOICE_POOL[allocated_voice_index % len(GLOBAL_VOICE_POOL)]
                persona_voice_registry[raw_persona_name] = target_actor
                allocated_voice_index += 1
            else:
                target_actor = persona_voice_registry[raw_persona_name]

            # DYNAMIC ACOUSTIC WEAVER: Map delivery strings to pitch/rate changes on the fly
            pitch_mod = "+0Hz"
            rate_mod = "+0%"
            
            if "deep" in delivery or "authoritative" in delivery:
                pitch_mod = "-15Hz"
                rate_mod = "-5%"
            elif "whisper" in delivery or "soft" in delivery:
                pitch_mod = "+12Hz"
                rate_mod = "-10%"
            elif "shouting" in delivery or "intense" in delivery or "rage" in delivery:
                pitch_mod = "-2Hz"
                rate_mod = "+22%"

            voice_filename = f"voice_segment_{idx}_{uuid.uuid4().hex[:4]}.mp3"
            voice_absolute_path = os.path.join(job_workspace_dir, voice_filename)
            
            logger.info(f"🎙️ Stage 2: Compiling [{raw_persona_name}] ({target_actor}) Style: [{delivery}] -> Pitch: {pitch_mod}, Rate: {rate_mod}")
            loop.run_until_complete(compile_parameter_voiceover(current_line, target_actor, pitch_mod, rate_mod, voice_absolute_path))
            voice_tracks_manifest.append(voice_absolute_path)
            
        loop.close()

        rendering_payload = {
            "video_path": file_path,
            "blueprint": normalized_blueprint,
            "voice_tracks": voice_tracks_manifest,
            "workspace_dir": job_workspace_dir,
            "voice_text": voice_text,
            "voice_actor": voice_actor
        }
        
        logger.info("🎬 Stage 3: Executing multi-track padding and audio filter mixers...")
        res_renderer = generate_proxy_worker.generate_proxy(rendering_payload)
        
        with open(result_file_path, "w") as f:
            json.dump({"state": "SUCCESS", "result": res_renderer}, f)
        
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

    unique_filename = f"upload_{uuid.uuid4().hex[:6]}.mp4"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    if video and video.filename:
        try:
            with open(file_path, "wb") as buffer:
                while content := await video.read(1024 * 1024):
                    buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File write failure: {str(e)}")
    else:
        sample_source = os.path.join(settings.BASE_DIR, "data/sample.mp4")
        if not os.path.exists(sample_source):
            raise HTTPException(status_code=400, detail="Missing baseline video file data source.")
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
