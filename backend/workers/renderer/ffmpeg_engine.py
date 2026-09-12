import os
import uuid
import ffmpeg
import logging
from backend.core.config import settings

logger = logging.getLogger("uvicorn.error")

class FfmpegProcessingEngine:
    def generate_proxy(self, tracker_data: dict):
        """
        PRODUCTION ROUGH-CUT: Physically extracts the highlight timestamps from the source video, 
        crops it to a mobile vertical canvas, and generates the lightweight preview proxy file.
        """
        video_path = tracker_data["video_path"]
        blueprint = tracker_data["blueprint"]
        
        if not blueprint:
            blueprint = [{"start": 0.0, "end": 3.0, "suggested_text": "Clip Preview"}]

        # Target the full length boundary of the highlight moment sequence
        start_cut = float(blueprint[0]["start"])
        end_cut = float(blueprint[-1]["end"])
        duration = end_cut - start_cut

        filename = os.path.basename(video_path)
        proxy_filename = f"proxy_{uuid.uuid4().hex[:8]}_{filename}"
        proxy_path = os.path.join(settings.PROXY_DIR, proxy_filename)
        
        try:
            logger.info(f"🎬 FFmpeg cutting master video segment from {start_cut}s to {end_cut}s...")
            # Physically slice out the dead space and compile the lightweight vertical canvas
            (
                ffmpeg
                .input(video_path, ss=start_cut, t=duration)
                .output(
                    proxy_path, 
                    vf="crop=ih*9/16:ih:(iw-ow)/2:0,scale=480:854", 
                    vcodec="libx264", 
                    preset="ultrafast", 
                    crf=26, 
                    acodec="aac"
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.info(f"✨ Rough-cut proxy compiled successfully: {proxy_path}")
        except ffmpeg.Error as e:
            logger.error(f"Proxy compilation failed: {e.stderr.decode()}")
            
        # Standardize timing baseline metrics to relative zero positions for the frontend player alignment
        normalized_blueprint = []
        for item in blueprint:
            normalized_blueprint.append({
                "text": item.get("suggested_text", "Watch!"),
                "start": max(0.0, float(item["start"]) - start_cut),
                "end": float(item["end"]) - start_cut,
                "x": item.get("x", 540),
                "y": item.get("y", 1400),
                "style": item.get("style", "impact-bold")
            })

        return {
            "status": "success",
            "proxy_url": f"/api/streams/{proxy_filename}",
            "original_video_path": video_path,
            "blueprint": normalized_blueprint
        }

    def render_final_export(self, composition_data: dict):
        """Bakes the high-resolution master crop."""
        video_path = composition_data["original_video_path"]
        blueprint = composition_data["blueprint"]
        
        filename = os.path.basename(video_path)
        output_filename = f"export_{uuid.uuid4().hex[:8]}_{filename}"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        # Calculate timeline duration
        duration = float(blueprint[-1]["end"]) - float(blueprint[0]["start"])
        crf_quality = getattr(settings, "EXPORT_CRF", 18)
        
        try:
            (
                ffmpeg
                .input(video_path, ss=float(blueprint[0]["start"]), t=duration)
                .output(
                    output_path,
                    vf="crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920",
                    vcodec="libx264",
                    preset="medium",
                    crf=crf_quality,
                    acodec="aac",
                    audio_bitrate="192k"
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return {"status": "completed", "export_filename": output_filename, "export_path": output_path}
        except ffmpeg.Error as e:
            raise Exception(f"Fidelity rendering failure: {e.stderr.decode()}")

generate_proxy_worker = FfmpegProcessingEngine()
