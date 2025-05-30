"""
Food Detection Module - Simplified
Handles YOLOv8 model loading and food detection from camera feed
"""

import cv2
import numpy as np
from ultralytics import YOLO
from config import Config
import time

class FoodDetector:
    def __init__(self):
        self.model = None
        self.pending_detections = {}  # Track pending detections waiting for confirmation
        self.load_model()
    
    def load_model(self):
        """Load YOLOv8 model"""
        try:
            self.model = YOLO(Config.MODEL_PATH)
            print(f"✅ Model loaded successfully from {Config.MODEL_PATH}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
    
    def detect_food(self, frame, draw_on_frame=False):
        """
        Detect food items in a frame
        
        Args:
            frame (np.ndarray): Input frame from camera
            draw_on_frame (bool): Whether to draw bounding boxes on the frame
            
        Returns:
            tuple: (processed_frame, detections_list, pending_detections)
        """
        if self.model is None:
            return frame, [], []
        
        # Run inference
        results = self.model(frame, conf=Config.CONFIDENCE_THRESHOLD)
        
        # Extract detections
        current_detections = []
        pending_detections = []
        processed_frame = frame.copy() if draw_on_frame else frame
        current_time = time.time()
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Get class name
                    if class_id < len(Config.FOOD_CLASSES):
                        food_name = Config.FOOD_CLASSES[class_id]
                        detection_key = f"{food_name}_{int(x1)}_{int(y1)}"
                        
                        # Check if this is a new detection or an existing pending one
                        if detection_key not in self.pending_detections:
                            # New detection, start tracking
                            self.pending_detections[detection_key] = {
                                "food": food_name,
                                "confidence": confidence,
                                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                "first_seen": current_time,
                                "confirmed": False
                            }
                        elif current_time - self.pending_detections[detection_key]["first_seen"] >= 0.5:  # Reduced from 2.0 to 0.5 seconds
                            # Detection has been present for 0.5 seconds, mark as pending
                            if not self.pending_detections[detection_key]["confirmed"]:
                                pending_detections.append({
                                    "food": food_name,
                                    "confidence": confidence,
                                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                                })
                        
                        # Draw bounding box if requested
                        if draw_on_frame:
                            processed_frame = self._draw_detection(
                                processed_frame, food_name, confidence, 
                                int(x1), int(y1), int(x2), int(y2)
                            )
        
        # Clean up old pending detections (older than 5 seconds)
        self.pending_detections = {
            k: v for k, v in self.pending_detections.items()
            if current_time - v["first_seen"] < 5.0
        }
        
        return processed_frame, current_detections, pending_detections
    
    def _draw_detection(self, frame, food_name, confidence, x1, y1, x2, y2):
        """Draw detection on frame (only used if draw_on_frame=True)"""
        # Simplified drawing function - just draw rectangle and label
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Prepare label
        label = f"{food_name}: {confidence:.2f}"
        
        # Draw label text
        cv2.putText(
            frame,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            1
        )
        
        return frame
    
    def get_camera_feed(self):
        """
        Get camera feed generator for streaming
        
        Yields:
            bytes: Encoded frame data
        """
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detect food in frame
                annotated_frame, detections, pending_detections = self.detect_food(frame)
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                frame_data = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        
        finally:
            cap.release()
    
    def process_single_frame(self, frame):
        """
        Process a single frame for detection
        
        Args:
            frame (np.ndarray): Input frame
            
        Returns:
            tuple: (annotated_frame, detections_list)
        """
        return self.detect_food(frame)