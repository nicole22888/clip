import os
import uuid
import ffmpeg
import asyncio
import json
import logging
import math
import shutil
from backend.core.config import settings
from backend.services.probe_and_validate import MediaProbeService
from backend.services.audio_mixer import AudioMixService

logger = logging.getLogger("uvicorn.error")

class DeterministicRenderPipeline:
    def _execute_production_quality_control(self, file_path: str, expected_duration: float) -> bool:
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 15000:
            return False
        try:
            probe = ffmpeg.probe(file_path)
            format_ctx = probe.get('format', {})
            actual_duration = float(format_ctx.get('duration', 0.0))
            if actual_duration <= 0:
                return False
            return True
        except Exception:
            return False

    async def _async_probe_duration(self, file_path: str) -> float:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await process.communicate()
        try: return float(stdout.decode().strip())
        except Exception: return 0.0

    def generate_proxy(self, tracker_data: dict):
        video_path = tracker_data["video_path"]
        blueprint = tracker_data["blueprint"]
        voice_tracks = tracker_data["voice_tracks"]
        workspace_dir = tracker_data["workspace_dir"]
        profile = settings.RENDER_PROFILE
        
        meta = MediaProbeService.probe_source(video_path)
        source_duration = meta["duration"]
        has_audio = meta["has_audio"]

        temp_segments = []
        accumulated_time = 0.0
        normalized_blueprint = []

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            for index, segment in enumerate(blueprint):
                start_cut = float(segment["start"])
                end_cut = float(segment["end"])
                text_content = str(segment["text"])

                # DEFENSIVE BOUNDARY GUARD: If an AI timestamp exceeds the video length, 
                # automatically skip it instead of letting FFmpeg render a broken empty file!
                if start_cut >= source_duration:
                    logger.info(f"⚠️ Segment #{index+1} start ({start_cut}s) exceeds video duration ({source_duration}s). Skipping segment safely.")
                    continue
                
                end_cut = min(end_cut, source_duration)
                duration = end_cut - start_cut
                if duration <= 0: continue
                
                seg_voice_path = voice_tracks[index % len(voice_tracks)]
                voice_duration = loop.run_until_complete(self._async_probe_duration(seg_voice_path))
                if voice_duration <= 0: voice_duration = duration
                
                pad_dur_sec = max(0.0, voice_duration - duration)
                track_length = duration + pad_dur_sec

                temp_seg_partial = os.path.join(workspace_dir, f"partial_seg_{index}.mp4")
                temp_seg_final = os.path.join(workspace_dir, f"final_seg_{index}.mp4")
                temp_segments.append(temp_seg_final)

                logger.info(f"🎬 Slicing Segment #{index+1}: {start_cut}s to {end_cut}s ({duration:.2f}s) -> Padding ({pad_dur_sec:.2f}s)")

                video_node = (
                    ffmpeg.input(video_path, ss=start_cut, t=duration).video
                    .filter('scale', r'iw*max(1080/iw\,1920/ih)', r'ih*max(1080/iw\,1920/ih)')
                    .filter('crop', 1080, 1920)
                    .filter('fps', fps=profile["fps"])
                    .filter('format', 'yuv420p')
                )
                if pad_dur_sec > 0:
                    video_node = video_node.filter('tpad', stop_mode='clone', stop_duration=pad_dur_sec)

                if has_audio:
                    game_audio_node = ffmpeg.input(video_path, ss=start_cut, t=duration).audio
                else:
                    game_audio_node = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=48000', f='lavfi', t=duration).audio

                final_mixed_audio = AudioMixService.process_and_mix_tracks(game_audio_node, seg_voice_path, pad_dur_sec, track_length)

                (
                    ffmpeg
                    .output(video_node, final_mixed_audio, temp_seg_partial, vcodec=profile["vcodec"], crf=profile["crf"], acodec=profile["acodec"])
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                os.rename(temp_seg_partial, temp_seg_final)

                normalized_blueprint.append({
                    "text": text_content,
                    "start": accumulated_time,
                    "end": accumulated_time + track_length,
                    "x": 540,
                    "y": 1400,
                    "style": "impact-bold"
                })
                accumulated_time += track_length

            if not temp_segments:
                raise Exception("No valid segments could be rendered within the video duration boundaries.")

            manifest_path = os.path.join(workspace_dir, "manifest.txt")
            with open(manifest_path, "w") as f:
                for tf in temp_segments: f.write(f"file '{os.path.abspath(tf)}'\n")

            partial_proxy_path = os.path.join(workspace_dir, "output.partial.mp4")
            (
                ffmpeg
                .input(manifest_path, format="concat", safe=0)
                .output(partial_proxy_path, vcodec="copy", acodec="copy")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            if not self._execute_production_quality_control(partial_proxy_path, accumulated_time):
                raise Exception("Production QC test failed.")

            final_proxy_filename = f"studio_compiled_{uuid.uuid4().hex[:6]}.mp4"
            final_proxy_destination = os.path.join(settings.PROXY_DIR, final_proxy_filename)
            os.rename(partial_proxy_path, final_proxy_destination)
            
            loop.close()
            return {
                "status": "success",
                "proxy_url": f"/api/streams/{final_proxy_filename}",
                "original_video_path": video_path,
                "blueprint": normalized_blueprint
            }
        except Exception as e:
            if loop.is_running(): loop.close()
            raise e

generate_proxy_worker = DeterministicRenderPipeline()
