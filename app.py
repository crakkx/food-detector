"""
Food Tracker - Main Flask Application
Simplified food detection and calorie tracking using YOLOv8
"""
import os
from flask import Flask, render_template, Response, jsonify, request
import cv2
import json
from datetime import datetime
import time

# Import our custom modules
from config import Config
from utils.food_detector import FoodDetector
from utils.calorie_mapper import CalorieMapper
from utils.file_handler import FileHandler

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
food_detector = FoodDetector()
calorie_mapper = CalorieMapper()
file_handler = FileHandler()

# Global variables for real-time detection
pending_detections = []

@app.route('/')
def index():
    """Home page with today's summary"""
    return render_template('index.html')

@app.route('/detect')
def detect():
    """Food detection page"""
    global camera_active, pending_detections
    camera_active = True  # Reset camera state
    pending_detections = []  # Clear pending detections
    return render_template('detect.html')

@app.route('/video_feed')
def video_feed():
    """Clean video streaming route - no overlays"""
    try:
        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )
    except Exception as e:
        print(f"Error in video_feed route: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_frames():
    """Generate clean video frames without overlays"""
    global pending_detections
    
    cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Run detection but don't draw on frame
            _, _, new_pending = food_detector.detect_food(frame, draw_on_frame=False)
            
            # Update pending detections
            if new_pending:
                pending_detections = new_pending
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Yield the frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
            # Slow down the frame rate a bit
            time.sleep(0.03)
            
    except Exception as e:
        print(f"Error in generate_frames: {str(e)}")
    finally:
        cap.release()

@app.route('/get_pending_detections')
def get_pending_detections():
    """Get current pending detections"""
    global pending_detections
    return jsonify({
        'detections': pending_detections
    })

@app.route('/log_detection', methods=['POST'])
def log_detection():
    """Log a detected food item"""
    data = request.json
    food_item = data.get('food')
    confidence = data.get('confidence', 0.0)
    
    if not food_item:
        return jsonify({'success': False, 'error': 'No food item specified'}), 400
    
    # Get calories for this food
    calories = calorie_mapper.get_calories(food_item)
    
    # Log the detection
    file_handler.log_detection(food_item, confidence, calories)
    
    return jsonify({
        'success': True,
        'food': food_item,
        'calories': calories
    })

@app.route('/get_daily_summary')
def get_daily_summary():
    """Get today's summary"""
    summary = file_handler.get_daily_summary()
    return jsonify(summary)

@app.route('/get_todays_items')
def get_todays_items():
    """Get all food items logged today"""
    items = file_handler.get_todays_detections()
    return jsonify({'items': items})

@app.route('/get_recent_detections')
def get_recent_detections():
    """Get recent detections"""
    items = file_handler.get_recent_detections(10)
    return jsonify({'items': items})

@app.route('/delete_detection/<detection_id>', methods=['POST'])
def delete_detection(detection_id):
    """Delete a food detection by its ID"""
    success = file_handler.delete_detection(detection_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Food item deleted successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to delete food item'
        }), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000)) 
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)
