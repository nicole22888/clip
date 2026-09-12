import os
import cv2
from celery import shared_task

@shared_task(bind=True)
def track_and_adjust(self, choreographer_data: dict):
    video_path = choreographer_data["video_path"]
    blueprint = choreographer_data["blueprint"]
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file missing for tracking: {video_path}")
        
    # Load OpenCV's lightweight Haar Cascade for fast face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(video_path)
    
    # Extract structural dimensions of the incoming media stream
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    for item in blueprint:
        start_ms = int(item["start"] * 1000)
        
        # Seek exactly to the millisecond where the action starts
        cap.set(cv2.CAP_PROP_POS_MSEC, start_ms)
        ret, frame = cap.read()
        
        if ret:
            # Convert to grayscale for fast processing cascade pass
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
            
            for (fx, fy, fw, fh) in faces:
                # Calculate normalized vertical height percentage (0.0 to 1.0)
                # This makes collision detection work regardless of 1080p, 4K, or 720p inputs
                vertical_percentage = (fy + fh) / frame_height
                
                # Collision Logic: If a face is resting in the bottom 40% of the screen
                if vertical_percentage > 0.60:
                    # Safely bump the layout text position up into the middle third of the vertical stack
                    item["y"] = 960  # Centers text clear of lower third face boxes
                    item["collision_detected"] = True
                    break 
                    
    cap.release()
    
    # Maintain uniform dictionary key structures across the entire factory pipeline
    return {"video_path": video_path, "blueprint": blueprint}
