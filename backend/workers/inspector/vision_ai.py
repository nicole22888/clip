import os
import json
import logging
import time
from google import genai
from google.genai import types
# Import the centralized secure settings anchor
from backend.core.config import settings

logger = logging.getLogger("uvicorn.error")

class GeminiVisionWorker:
    def run(self, video_path: str, user_prompt: str):
        """
        Enterprise-grade multi-modal inspector. Safely accesses keys 
        from the absolute settings configuration object layer.
        """
        # CRITICAL FIX: Pulls key cleanly from the shared absolute configurations settings layer
        api_key = settings.GEMINI_API_KEY

        if not api_key or api_key == "AIzaSyYOUR_ACTUAL_GEMINI_KEY_HERE":
            logger.error("❌ CRITICAL: Missing valid GEMINI_API_KEY inside centralized configuration settings object.")
            return self._fallback(video_path, user_prompt)

        try:
            client = genai.Client(api_key=api_key)
            logger.info(f"Staging binary clip onto Google AI File Service: {video_path}")
            video_file_node = client.files.upload(file=video_path)
            
            while video_file_node.state.name == "PROCESSING":
                logger.info("Waiting for Google file processing encoder layout to finalize...")
                time.sleep(2)
                video_file_node = client.files.get(name=video_file_node.name)

            system_instruction = (
                "You are an expert viral gaming video editor. Analyze both the audio tracks and video frames of this footage.\n"
                "1. Find the highest energy highlight moment based on gunshots, game audio fireworks, shouting, anger, or extreme action.\n"
                "2. Cut exactly around that highlight. Return a meticulous, tight JSON array timeline where you split "
                "the spoken words or hype audio events into ultra-short, fast-switching caption objects (1-3 words per chunk).\n\n"
                "Return ONLY a clean JSON list matching this exact format with zero markdown syntax or wrapping:\n"
                '[{"start": 1.2, "end": 1.8, "mood": "action", "style": "impact-bold", "suggested_text": "LETS GO!"}]'
            )

            logger.info("Invoking Gemini 2.5 Flash timeline analysis matrix...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[video_file_node, f"Directorial instructions: {user_prompt}"],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            raw_text = response.text
            clean_json = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
            analysis_data = json.loads(clean_json)

            client.files.delete(name=video_file_node.name)
            return {"video_path": video_path, "analysis": analysis_data, "user_prompt": user_prompt}

        except Exception as e:
            logger.error(f"Gemini Processing Exception: {str(e)}")
            return self._fallback(video_path, user_prompt)

    def _fallback(self, video_path, user_prompt):
        return {
            "video_path": video_path,
            "analysis": [
                {"start": 0.2, "end": 1.5, "mood": "action", "style": "impact-bold", "suggested_text": "OH MY GOD!"},
                {"start": 1.6, "end": 2.8, "mood": "action", "style": "impact-bold", "suggested_text": "UNREAL CLIP!"},
                {"start": 2.9, "end": 4.5, "mood": "action", "style": "impact-bold", "suggested_text": "LETS GOOOOO!"}
            ],
            "user_prompt": user_prompt
        }

analyze_video = GeminiVisionWorker()
