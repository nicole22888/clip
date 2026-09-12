from celery import shared_task

@shared_task(bind=True)
def calculate_layout(self, inspector_data: dict):
    video_path = inspector_data["video_path"]
    analysis = inspector_data["analysis"]
    user_prompt = inspector_data.get("user_prompt", "")
    
    blueprint = []
    
    for moment in analysis:
        # Standard positioning assuming a 9:16 vertical video layout (1080x1920)
        # Default text to center-bottom of the screen
        x_pos = 540 
        y_pos = 1400 
        
        # Determine the visual style based on Worker 1's mood detection
        style = "impact-bold" if moment.get("mood") in ["energetic", "action"] else "smooth-fade"
        
        # Fallback: Use the user's custom text if provided, else use AI suggestion
        text_to_render = user_prompt if user_prompt else moment.get("suggested_text", "Watch this!")
        
        blueprint.append({
            "text": text_to_render,
            "start": moment["start"],
            "end": moment["end"],
            "x": x_pos,
            "y": y_pos,
            "style": style
        })
        
    # Pass the calculated geometric blueprint to the next worker
    return {"video_path": video_path, "blueprint": blueprint}
