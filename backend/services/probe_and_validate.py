import ffmpeg
import logging
import math

logger = logging.getLogger("uvicorn.error")

class MediaProbeService:
    @staticmethod
    def probe_source(video_path: str) -> dict:
        """Defensively analyzes container metadata to check for streams validity."""
        try:
            probe = ffmpeg.probe(video_path)
            format_ctx = probe.get('format', {})
            
            # Robust boundary checks against missing/N/A duration properties
            duration_raw = format_ctx.get('duration')
            if duration_raw is None or duration_raw == "N/A":
                # Fallback to structural calculations if master duration metadata is corrupted
                video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
                if video_stream and 'duration' in video_stream:
                    duration = float(video_stream['duration'])
                else:
                    raise ValueError("Inherent media duration metric is missing or unreadable.")
            else:
                duration = float(duration_raw)
                
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("Encountered an invalid, infinite, or zero duration container metric.")

            has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])
            
            return {
                "duration": duration,
                "has_audio": has_audio,
                "probe_raw": probe
            }
        except Exception as e:
            logger.error(f"Media Prober Core Failure: {str(e)}")
            raise ValueError(f"Durable media probing operation failed: {str(e)}")

    @staticmethod
    def validate_and_normalize_blueprint(blueprint: list, source_duration: float) -> list:
        """Sorts, strips overlaps, checks boundaries, and handles NaN configurations cleanly."""
        if not blueprint:
            return [{"start": 0.0, "end": min(4.0, source_duration), "text": "Clip Highlight"}]
            
        cleaned = []
        for item in blueprint:
            try:
                start = float(item.get("start", 0.0))
                end = float(item.get("end", 0.0))
                text = str(item.get("text", "Highlight")).strip()
                
                if not math.isfinite(start) or not math.isfinite(end): continue
                if start < 0 or end <= start or start >= source_duration: continue
                
                # Constrain boundary overflow endpoints dynamically
                end = min(end, source_duration)
                cleaned.append({"start": start, "end": end, "text": text})
            except Exception:
                continue
                
        if not cleaned:
            return [{"start": 0.0, "end": min(4.0, source_duration), "text": "Clip Highlight"}]
            
        # Sort chronologically to safely execute chronological tracking
        cleaned.sort(key=lambda x: x["start"])
        
        # OVERSITE REJECTION: Enforce native normalization for overlapping segments
        normalized = []
        previous = None
        for current in cleaned:
            if previous is not None:
                if current["start"] < previous["end"]:
                    # Adjust current clip start boundary to remove overlapping artifacts
                    current["start"] = previous["end"]
                    if current["end"] <= current["start"]:
                        continue # Skip entirely if swallowed by the previous clip window
            normalized.append(current)
            previous = current
            
        return normalized if normalized else [{"start": 0.0, "end": min(4.0, source_duration), "text": "Clip Highlight"}]
