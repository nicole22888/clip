import edge_tts
import logging

logger = logging.getLogger("uvicorn.error")

class VoiceoverService:
    @staticmethod
    async def generate_speech_file(text: str, voice: str, target_path: str):
        """Bakes premium neural narration onto an explicit .mp3 file target container structure."""
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(target_path)
            logger.info(f"✨ Successfully generated clean narration snippet audio track: {target_path}")
        except Exception as e:
            logger.error(f"Voiceover track compilation failed: {str(e)}")
            raise e
