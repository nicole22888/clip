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
            
            duration_raw = format_ctx.get('duration')
            if duration_raw is None or duration_raw == "N/A":
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
        """Sorts, strips overlaps, checks boundaries, and strictly enforces string-keyed dictionary primitives output."""
        fallback_blueprint = [{"start": 0.0, "end": min(4.0, source_duration), "character_persona": "Character 1", "audio_fx": "clean_studio", "text": "Clip Highlight"}]
        
        if not blueprint:
            return fallback_blueprint
            
        cleaned = []
        for item in blueprint:
            try:
                # Type coerce whatever structure is present into clean primitives variables
                if isinstance(item, dict):
                    d = item
                elif hasattr(item, "model_dump"):
                    d = item.model_dump()
                elif hasattr(item, "__dict__"):
                    d = vars(item)
                else:
                    continue

                start = float(d.get("start", 0.0))
                end = float(d.get("end", 0.0))
                text = str(d.get("text", d.get("suggested_text", "Highlight"))).strip()
                persona = str(d.get("character_persona", "Character 1")).strip()
                audio_fx = str(d.get("audio_fx", "clean_studio")).strip()
                vocal_delivery = str(d.get("vocal_delivery", "normal")).strip()
                
                if not math.isfinite(start) or not math.isfinite(end): continue
                if start < 0 or end <= start or start >= source_duration: continue
                
                end = min(end, source_duration)
                
                # ENFORCE STRING KEYS DICTIONARY NATIVELY RIGHT HERE
                cleaned.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "character_persona": persona,
                    "audio_fx": audio_fx,
                    "vocal_delivery": vocal_delivery
                })
            except Exception:
                continue
                
        if not cleaned:
            return fallback_blueprint
            
        cleaned.sort(key=lambda x: x["start"])
        
        normalized = []
        previous = None
        for current in cleaned:
            if previous is not None:
                if current["start"] < previous["end"]:
                    current["start"] = previous["end"]
                    if current["end"] <= current["start"]:
                        continue
            normalized.append(current)
            previous = current
            
        return normalized if normalized else fallback_blueprint
