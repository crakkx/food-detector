import os

class Config:
    # Model configuration
    MODEL_PATH = "models/best.pt"
    
    # Camera configuration
    CAMERA_INDEX = 0  # Default webcam
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    
    # Detection configuration
    CONFIDENCE_THRESHOLD = 0.5
    DETECTION_COOLDOWN = 3  # seconds between logging same food item
    
    # Data storage paths
    DATA_DIR = "data"
    CALORIE_LOGS_FILE = os.path.join(DATA_DIR, "calorie_logs.json")
    DETECTION_HISTORY_FILE = os.path.join(DATA_DIR, "detection_history.json")
    
    # Flask configuration
    SECRET_KEY = "your-secret-key-here"
    DEBUG = True
    
    # Food classes (your trained model classes)
    FOOD_CLASSES = [
        "Apple", "Banana", "Watermelon", "Strawberry", "Orange",
        "Bread", "Carrot", "Cucumber", "Broccoli", "Pizza"
    ]