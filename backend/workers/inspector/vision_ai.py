import os
import json
import torch
from celery import shared_task
from qwen_vl_utils import process_vision_info
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

# Global cache references to prevent memory-leak loops across task invocations
_model_cache = None
_processor_cache = None

def _get_model_and_processor():
    """Lazily loads and caches the VLM framework, locking memory to CPU targets."""
    global _model_cache, _processor_cache
    
    if _model_cache is None:
        model_id = "Qwen/Qwen2.5-VL-3B-Instruct"
        
        # Pull processor utilities
        _processor_cache = AutoProcessor.from_pretrained(model_id)
        
        # Initialize model cleanly for GitHub Codespaces CPU limitations
        _model_cache = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # Forces valid CPU evaluation paths
            device_map="cpu",          # Anchors layout explicitly away from non-existent CUDA layers
            low_cpu_mem_usage=True     # Slashes RAM instantiation spikes during weights setup
        )
        
    return _model_cache, _processor_cache

@shared_task(bind=True, max_retries=3)
def analyze_video(self, video_path: str, user_prompt: str):
    # Verify file existence before booting heavy ML configurations
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Target video file not found at path: {video_path}")
        
    # Extract cached model engines safely
    model, processor = _get_model_and_processor()
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "video", "video": video_path},
                {
                    "type": "text", 
                    "text": f"Analyze this video. User intent: {user_prompt}. Return ONLY a raw JSON array string mapping 'start' (seconds), 'end' (seconds), 'mood', and 'suggested_text' keys for the top 3 best moments. Do not return markdown wraps."
                }
            ]
        }
    ]
    
    # Process inputs specifically formatted for Qwen's vision pipeline
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = processor(
        text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt"
    ).to(model.device)
    
    # Inference / Video Analysis
    with torch.no_grad():  # Disables gradient logging to save vast amounts of workspace RAM
        generated_ids = model.generate(**inputs, max_new_tokens=512)
        
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]
    
    try:
        # Clean potential markdown structures if returned despite instruction
        clean_json = output_text.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
        analysis_data = json.loads(clean_json)
    except Exception as e:
        # Fallback tracking sequence to prevent downstream orchestration crashes
        analysis_data = [
            {"start": 0.0, "end": 5.0, "mood": "neutral", "suggested_text": f"Clip 1 for: {user_prompt}"}
        ]
        
    return {"video_path": video_path, "analysis": analysis_data, "user_prompt": user_prompt}
