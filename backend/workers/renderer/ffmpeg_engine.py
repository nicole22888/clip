import os
import uuid
import ffmpeg
import asyncio
import logging
import edge_tts
from backend.core.config import settings

logger = logging.getLogger("uvicorn.error")

class FfmpegProcessingEngine:
    async def _generate_voiceover(self, text: str, voice: str, output_path: str):
        """Generates premium neural human narration using the exact voice profile selected by the user."""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    def generate_proxy(self, tracker_data: dict):
        """
        CAPCUT ENTERPRISE LAYER: Generates the user's custom voice script choice, 
        ducks background gameplay levels, and stitches multi-clip compilations back-to-back.
        """
        video_path = tracker_data["video_path"]
        blueprint = tracker_data["blueprint"]
        voice_text = tracker_data.get("voice_text", "Check out this gaming action compilation highlight sequence!")
        voice_actor = tracker_data.get("voice_actor", "en-US-ChristopherNeural")

        if not blueprint:
            blueprint = [{"start": 0.0, "end": 4.0, "text": "Clip Highlight"}]

        filename = os.path.basename(video_path)
        proxy_filename = f"studio_edit_{uuid.uuid4().hex[:8]}_{filename}"
        proxy_path = os.path.join(settings.PROXY_DIR, proxy_filename)
        
        # 1. Generate the Custom Neural Voiceover script track using the selected voice profile
        voiceover_path = os.path.join(settings.PROXY_DIR, f"voice_{uuid.uuid4().hex[:6]}.mp3")
        logger.info(f"🎙️ Contacting Neural Network voice profile: {voice_actor}...")
        asyncio.run(self._generate_voiceover(voice_text, voice_actor, voiceover_path))

        temp_segments = []
        accumulated_time = 0.0
        normalized_blueprint = []

        try:
            # 2. Slice out the dynamic high-energy visual scenes
            for index, segment in enumerate(blueprint):
                start_cut = float(segment["start"])
                end_cut = float(segment["end"])
                duration = end_cut - start_cut
                
                if duration <= 0: continue
                
                temp_seg = os.path.join(settings.PROXY_DIR, f"t_seg_{index}_{uuid.uuid4().hex[:4]}.mp4")
                temp_segments.append(temp_seg)
                
                (
                    ffmpeg
                    .input(video_path, ss=start_cut, t=duration)
                    .output(temp_seg, vf="crop=ih*9/16:ih:(iw-ow)/2:0,scale=480:854", vcodec="libx264", preset="ultrafast", crf=26, acodec="aac")
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                normalized_blueprint.append({
                    "text": segment.get("text", "Highlight!"),
                    "start": accumulated_time,
                    "end": accumulated_time + duration,
                    "x": 540,
                    "y": 1350,
                    "style": "impact-bold"
                })
                accumulated_time += duration

            # 3. Join the visual files back-to-back
            manifest_path = os.path.join(settings.PROXY_DIR, f"man_{uuid.uuid4().hex[:6]}.txt")
            with open(manifest_path, "w") as f:
                for tf in temp_segments:
                    f.write(f"file '{os.path.abspath(tf)}'\n")

            video_only_output = os.path.join(settings.PROXY_DIR, f"v_only_{uuid.uuid4().hex[:6]}.mp4")
            (
                ffmpeg
                .input(manifest_path, format="concat", safe=0)
                .output(video_only_output, vcodec="libx264", acodec="aac")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            logger.info("🎛️ Audio Mixing: Blending game tracks with customized neural voice...")
            # 4. ENTERPRISE AUDIO MIXING BLOCK (Ducks game audio, layers customized character voice)
            video_input = ffmpeg.input(video_only_output)
            audio_voice = ffmpeg.input(voiceover_path)

            mixed_audio = ffmpeg.filter(
                [video_input.audio, audio_voice.audio], 
                'amix', 
                inputs=2, 
                duration='first', 
                weights='1 2.8' # Boosts custom voice track clarity while dampening explosion decibels
            )

            (
                ffmpeg
                .output(video_input.video, mixed_audio, proxy_path, vcodec="copy", acodec="aac")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            # Clean structural directory cache spaces completely
            os.remove(manifest_path)
            os.remove(video_only_output)
            os.remove(voiceover_path)
            for tf in temp_segments:
                if os.path.exists(tf): os.remove(tf)

            logger.info(f"✨ Production Compilation Fully Assembled: {proxy_path}")
            return {
                "status": "success",
                "proxy_url": f"/api/streams/{proxy_filename}",
                "original_video_path": video_path,
                "blueprint": normalized_blueprint
            }

        except ffmpeg.Error as e:
            logger.error(f"Mixing engine failed: {e.stderr.decode()}")
            return {"status": "error", "message": "Pipeline mixing failure"}

    def render_final_export(self, composition_data: dict):
        return {"status": "completed", "export_filename": "final_studio_master.mp4", "export_path": ""}

generate_proxy_worker = FfmpegProcessingEngine()
