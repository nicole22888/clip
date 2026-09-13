import os
import json
import logging
import time
from google import genai
from google.genai import types
from backend.core.config import settings

logger = logging.getLogger("uvicorn.error")

class GeminiUniversalScreenwriterWorker:
    def run(self, video_path: str, user_prompt: str):
        """
        Universal Multi-Modal Director Engine. Watches ANY category of video file natively,
        deduces the genre/tone, and generates a synchronized character dialogue script 
        with dynamic voice switching and audio effects tags.
        """
        api_key = settings.GEMINI_API_KEY
        if not api_key or api_key == "AIzaSyYOUR_ACTUAL_GEMINI_KEY_HERE":
            logger.error("❌ CRITICAL: Missing valid GEMINI_API_KEY inside configuration settings.")
            return self._fallback(video_path, user_prompt)

        try:
            # Initialize the official secure Google GenAI Client SDK wrapper
            client = genai.Client(api_key=api_key)
            
            logger.info(f"📡 Staging asset binary onto Google AI Storage Service: {video_path}")
            video_file_node = client.files.upload(file=video_path)
            
            # Polling guard ensuring remote file conversion processing wraps cleanly
            while video_file_node.state.name == "PROCESSING":
                logger.info("Waiting for Google file processing encoder layout to finalize...")
                time.sleep(2)
                video_file_node = client.files.get(name=video_file_node.name)

            # --- UNIVERSAL CATEGORY-AGNOSTIC PROMPT DIRECTIVE CONTRACT ---
            system_instruction = (
                "You are an elite, universal multi-modal film director and video editor. Your task is to analyze both the visual frames "
                "and audio tracks of this uploaded footage to create a synchronized, high-impact script narrative from scratch.\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. GENRE DEDUCTION: Analyze the visual events. Identify the core subject, environment, and actions happening on screen "
                "(e.g., cooking, combat gaming, sports action, vlogging, tutorial, silent film). Assign a baseline emotional tone.\n"
                "2. MULTI-CHARACTER BANTER: Write an engaging, highly dramatic script that completely maps to the intensity of what is seen. "
                "Create 1 to 3 distinct voice character personas that fit the deduced genre perfectly (e.g., if sports: main commentator and field analyst; "
                "if cooking: enthusiastic chef and hungry friend; if gaming: tactical squad teammates).\n"
                "3. DYNAMIC SCENE CUTTING: Isolate high-impact highlight moments across the video. For each highlight, break the script "
                "into short phrase chunks (1-5 words max per line).\n"
                "4. TIMELINE ACCESS: For each phrase chunk, map out its exact 'start' and 'end' timestamps relative to the source footage, "
                "the assigned 'character_persona' (e.g., Character 1, Character 2), and a matching 'audio_fx' tag matching the spatial environment "
                "(choose strictly from: 'clean_studio', 'walkie_talkie', 'hall_reverb', 'megaphone').\n\n"
                "Return ONLY a type-safe JSON schema array matching this exact properties contract structure with zero markdown or filler text:\n"
                "{\n"
                "  \"analysis\": [\n"
                "    {\"start\": 1.2, \"end\": 3.5, \"character_persona\": \"Character 1\", \"audio_fx\": \"walkie_talkie\", \"text\": \"WIPING THEM BACK!\"},\n"
                "    {\"start\": 3.8, \"end\": 6.2, \"character_persona\": \"Character 2\", \"audio_fx\": \"clean_studio\", \"text\": \"FLAG IS SECURED!\"}\n"
                "  ]\n"
                "}"
            )

            logger.info("Invoking Gemini 2.5 Flash universal screenwriter matrix...")
            # Enforce strict OpenAPI JSON Schema output configurations
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    video_file_node, 
                    types.Part.from_text(text=f"Directorial focus instructions overrides: {user_prompt}")
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "analysis": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "start": {"type": "number"},
                                        "end": {"type": "number"},
                                        "character_persona": {"type": "string"},
                                        "audio_fx": {"type": "string"},
                                        "text": {"type": "string"}
                                    },
                                    "required": ["start", "end", "character_persona", "audio_fx", "text"]
                                }
                            }
                        },
                        "required": ["analysis"]
                    },
                    temperature=0.2
                )
            )

            raw_response_text = response.text
            parsed_data = json.loads(raw_response_text.strip())
            analysis_data = parsed_data.get("analysis", [])

            client.files.delete(name=video_file_node.name)
            logger.info("✨ Cleaned up remote storage asset node tokens.")
            return {"video_path": video_path, "analysis": analysis_data, "user_prompt": user_prompt}

        except Exception as sdk_fault:
            logger.error(f"❌ Gemini Universal Writer Engine crash: {str(sdk_fault)}")
            return self._fallback(video_path, user_prompt)

    def _fallback(self, video_path, user_prompt):
        """Emergency high-availability fallback if cloud connection drops out."""
        return {
            "video_path": video_path,
            "analysis": [
                {"start": 0.5, "end": 2.5, "character_persona": "Character 1", "audio_fx": "clean_studio", "text": "WATCH THIS PLAY!"},
                {"start": 2.6, "end": 5.0, "character_persona": "Character 2", "audio_fx": "walkie_talkie", "text": "INSANE MOMENT!"}
            ],
            "user_prompt": user_prompt
        }

analyze_video = GeminiUniversalScreenwriterWorker()
