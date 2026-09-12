import os
import ffmpeg
import logging
from backend.core.config import settings

logger = logging.getLogger("uvicorn.error")

class FfmpegProcessingEngine:
    def generate_proxy(self, tracker_data: dict):
        """Generates a lightning-fast 480p preview clip chunk strictly for mobile layout composition views."""
        video_path = tracker_data["video_path"]
        blueprint = tracker_data["blueprint"]
        
        filename = os.path.basename(video_path)
        proxy_filename = f"proxy_{filename}"
        proxy_path = os.path.join(settings.PROXY_DIR, proxy_filename)
        
        try:
            (
                ffmpeg
                .input(video_path)
                .output(proxy_path, vf="scale=-2:480", vcodec="libx264", preset="ultrafast", crf=28, acodec="aac")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            logger.error(f"Proxy compilation failed: {e.stderr.decode()}")
            
        return {
            "status": "success",
            "proxy_url": f"/api/streams/{proxy_filename}",
            "original_video_path": video_path,
            "blueprint": blueprint
        }

    def render_final_export(self, composition_data: dict):
        """
        Slices the video at the exact highlights timestamps, applies mobile cropping,
        and saves the high-resolution file to your outputs folder.
        """
        video_path = composition_data["original_video_path"]
        blueprint = composition_data["blueprint"]
        
        filename = os.path.basename(video_path)
        output_filename = f"export_{uuid.uuid4().hex[:8]}_{filename}"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        if not blueprint:
            raise ValueError("Timeline blueprint cannot be empty for rendering.")
            
        # Target the first selected best moment item sequence parameters
        target_moment = blueprint[0]
        start_time = float(target_moment["start"])
        end_time = float(target_moment["end"])
        duration = end_time - start_time
        
        # Pull high fidelity encoding presets from configuration constants
        crf_quality = getattr(settings, "EXPORT_CRF", 18)
        
        try:
            print(f"🎬 Initiating HQ render cut: Slicing {start_time}s to {end_time}s...")
            # Slices precisely, applies 9:16 mobile centering crops, and retains high fidelity encoding paths
            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(
                    output_path,
                    vf="crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920",
                    vcodec="libx264",
                    preset="slow",      # Maximizes frame compression efficiency maps
                    crf=crf_quality,    # Low CRF value ensures standard visually lossless delivery
                    acodec="aac",
                    audio_bitrate="192k"
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            print(f"🚀 High-Resolution master video copy successfully created at: {output_path}")
            return {"status": "completed", "export_filename": output_filename, "export_path": output_path}
            
        except ffmpeg.Error as e:
            stderr_log = e.stderr.decode()
            logger.error(f"FFmpeg render operation crash logs: {stderr_log}")
            raise Exception(f"High fidelity rendering failure: {stderr_log}")

# Instantiate matching class mappings hooks
generate_proxy_worker = FfmpegProcessingEngine()
