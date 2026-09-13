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
        """Rigorously inspects contract properties to catch bad renders before publishing asset tokens."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 15000:
            return False
        try:
            probe = ffmpeg.probe(file_path)
            format_ctx = probe.get('format', {})
            actual_duration = float(format_ctx.get('duration', 0.0))
            
            if abs(actual_duration - expected_duration) > 0.8:
                logger.error(f"QC REJECTION: Duration deviation exceeds contract limits. Expected: {expected_duration}s, Got: {actual_duration}s")
                return False
                
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
            
            if not video_stream or not audio_stream: return False
            if int(video_stream['width']) != 1080 or int(video_stream['height']) != 1920: return False
            if video_stream['pix_fmt'] != 'yuv420p': return False
            
            return True
        except Exception:
            return False

    async def _async_probe_duration(self, file_path: str) -> float:
        """Natively executes ffprobe inside an async subprocess to eliminate thread-blocking operations."""
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        try:
            return float(stdout.decode().strip())
        except Exception:
            return 0.0

    def generate_proxy(self, tracker_data: dict):
        video_path = tracker_data["video_path"]
        blueprint = tracker_data["blueprint"]
        voice_tracks = tracker_data["voice_tracks"]
        workspace_dir = tracker_data["workspace_dir"]

        profile = settings.RENDER_PROFILE
        
        meta = MediaProbeService.probe_source(video_path)
        source_duration = meta["duration"]
        has_audio = meta["has_audio"]
        
        validated_blueprint = MediaProbeService.validate_and_normalize_blueprint(blueprint, source_duration)

        temp_segments = []
        accumulated_time = 0.0
        normalized_blueprint = []

        # Build a temporary internal async loop runner for the nested pipeline operations
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            for index, segment in enumerate(validated_blueprint):
                start_cut = segment["start"]
                end_cut = segment["end"]
                duration = end_cut - start_cut
                
                seg_voice_path = voice_tracks[index % len(voice_tracks)]
                
                # ASYNC PROBER DEPLOYMENT: Non-blocking tracking abstraction layer
                voice_duration = loop.run_until_complete(self._async_probe_duration(seg_voice_path))
                if voice_duration <= 0:
                    voice_duration = duration
                
                pad_dur_sec = max(0.0, voice_duration - duration)
                track_length = duration + pad_dur_sec

                temp_seg_partial = os.path.join(workspace_dir, f"partial_seg_{index}.mp4")
                temp_seg_final = os.path.join(workspace_dir, f"final_seg_{index}.mp4")
                temp_segments.append(temp_seg_final)

                logger.info(f"🎬 Processing Segment #{index+1}: Visual Slicing ({duration:.2f}s) -> Padding ({pad_dur_sec:.2f}s)")

                video_node = (
                    ffmpeg.input(video_path, ss=start_cut, t=duration).video
                    .filter('scale', 'iw*max(1080/iw\,1920/ih)', 'ih*max(1080/iw\,1920/ih)')
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

                final_mixed_audio = AudioMixService.process_and_mix_tracks(
                    game_audio_node, seg_voice_path, pad_dur_sec, track_length
                )

                (
                    ffmpeg
                    .output(video_node, final_mixed_audio, temp_seg_partial, vcodec=profile["vcodec"], crf=profile["crf"], acodec=profile["acodec"])
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                os.rename(temp_seg_partial, temp_seg_final)

                normalized_blueprint.append({
                    "text": segment["text"],
                    "start": accumulated_time,
                    "end": accumulated_time + track_length,
                    "x": 540,
                    "y": 1400,
                    "style": "impact-bold"
                })
                accumulated_time += track_length

            manifest_path = os.path.join(workspace_dir, "manifest.txt")
            with open(manifest_path, "w") as f:
                for tf in temp_segments:
                    f.write(f"file '{os.path.abspath(tf)}'\n")

            partial_proxy_path = os.path.join(workspace_dir, "output.partial.mp4")
            (
                ffmpeg
                .input(manifest_path, format="concat", safe=0)
                .output(partial_proxy_path, vcodec="copy", acodec="copy")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            if not self._execute_production_quality_control(partial_proxy_path, accumulated_time):
                raise Exception("Production Quality Control Inspection Rejected the generated container properties.")

            final_proxy_filename = f"studio_compiled_{uuid.uuid4().hex[:6]}.mp4"
            final_proxy_destination = os.path.join(settings.PROXY_DIR, final_proxy_filename)
            
            os.rename(partial_proxy_path, final_proxy_destination)
            logger.info(f"✨ Production Clip Compilation Successfully Published: {final_proxy_destination}")
            
            loop.close()
            return {
                "status": "success",
                "proxy_url": f"/api/streams/{final_proxy_filename}",
                "original_video_path": video_path,
                "blueprint": normalized_blueprint
            }

        except ffmpeg.Error as e:
            loop.close()
            logger.error(f"FFmpeg Graph Processing Engine fault: {e.stderr.decode()}")
            raise Exception(f"FFmpeg Internal Loop Failure: {e.stderr.decode()}")

generate_proxy_worker = DeterministicRenderPipeline()
