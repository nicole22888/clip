import os
import json
import torch
from celery import shared_task
from qwen_vl_utils import process_vision_info
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

_model_cache = None
_processor_cache = None

def _get_model_and_processor():
    """Lazily loads and caches the 2B VLM framework, optimized for cloud CPUs."""
    global _model_cache, _processor_cache
    
    if _model_cache is None:
        # Swap to the optimized 2B parameter version to maximize processing speeds
        model_id = "Qwen/Qwen2-VL-2B-Instruct"
        
        _processor_cache = AutoProcessor.from_pretrained(model_id)
        _model_cache = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        
    return _model_cache, _processor_cache

@shared_task(bind=True, max_retries=3)
def analyze_video(self, video_path: str, user_prompt: str):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Target video file not found at path: {video_path}")
        
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
    
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    inputs = processor(
        text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt"
    ).to(model.device)
    
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=512)
        
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]
    
    try:
        clean_json = output_text.strip()
        if clean_json.startswith("```"):
            clean_json = clean_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
        analysis_data = json.loads(clean_json)
    except Exception as e:
        analysis_data = [
            {"start": 0.0, "end": 5.0, "mood": "neutral", "suggested_text": f"Clip 1 for: {user_prompt}"}
        ]
        
    return {"video_path": video_path, "analysis": analysis_data, "user_prompt": user_prompt}
