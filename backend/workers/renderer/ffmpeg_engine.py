import os
import ffmpeg
from celery import shared_task
from core.config import settings

@shared_task(bind=True)
def generate_proxy(self, tracker_data: dict):
    """Generates a lightweight, highly compressed 480p proxy for immediate streaming."""
    video_path = tracker_data["video_path"]
    blueprint = tracker_data["blueprint"]  # Fixed key matching tracker output
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Source video missing for proxy generation: {video_path}")
        
    filename = os.path.basename(video_path)
    proxy_filename = f"proxy_{filename}"
    proxy_path = os.path.join(settings.PROXY_DIR, proxy_filename)
    
    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                proxy_path, 
                vf="scale=-2:480", 
                vcodec="libx264", 
                preset="ultrafast", 
                crf=28, 
                acodec="aac"
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        stderr_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
        raise Exception(f"FFmpeg proxy generation failed: {stderr_msg}")
    
    return {
        "status": "success",
        "proxy_url": f"/api/streams/{proxy_filename}",
        "proxy_path": proxy_path,
        "original_video_path": video_path,
        "blueprint": blueprint
    }

@shared_task(bind=True)
def render_final_export(self, composition_data: dict):
    """Cuts the video to specific timestamps and burns it into a clean vertical output."""
    video_path = composition_data["original_video_path"]
    blueprint = composition_data["blueprint"]
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Source video missing for final export: {video_path}")
        
    filename = os.path.basename(video_path)
    output_filename = f"export_{filename}"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    # Take the first highlighted moment from our tracking blueprint to clip
    if not blueprint:
        raise ValueError("Cannot render video export with an empty blueprint timeline.")
        
    best_moment = blueprint[0]
    start_time = best_moment["start"]
    duration = best_moment["end"] - start_time
    
    try:
        # FFmpeg pipeline: Slice precisely by time, crop into a 9:16 mobile canvas shape,
        # and encode using production-ready delivery configurations.
        (
            ffmpeg
            .input(video_path, ss=start_time, t=duration)
            .output(
                output_path,
                vf="crop=ih*9/16:ih:(iw-ow)/2:0,scale=1080:1920",
                vcodec="libx264",
                preset="medium",
                crf=22,
                acodec="aac",
                audio_bitrate="192k"
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        stderr_msg = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
        raise Exception(f"FFmpeg final export render failed: {stderr_msg}")
        
    return {
        "status": "completed",
        "export_filename": output_filename,
        "export_path": output_path
    }
