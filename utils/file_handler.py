"""
File Handler Module
Handles JSON file operations for data persistence
"""

import json
import os
from datetime import datetime, date
from config import Config

class FileHandler:
    def __init__(self):
        self.calorie_logs_file = Config.CALORIE_LOGS_FILE
        self.detection_history_file = Config.DETECTION_HISTORY_FILE
        self._ensure_data_directory()
        self._initialize_files()
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(Config.DATA_DIR):
            os.makedirs(Config.DATA_DIR)
    
    def _initialize_files(self):
        """Initialize JSON files if they don't exist"""
        if not os.path.exists(self.calorie_logs_file):
            self._write_json(self.calorie_logs_file, {})
        
        if not os.path.exists(self.detection_history_file):
            self._write_json(self.detection_history_file, [])
    
    def _read_json(self, file_path):
        """Read and parse JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} if 'logs' in file_path else []
    
    def _write_json(self, file_path, data):
        """Write data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def log_detection(self, food_item, confidence, calories):
        """
        Log a new food detection
        
        Args:
            food_item (str): Detected food name
            confidence (float): Detection confidence
            calories (int): Calorie count for the food
        """
        # Add to detection history
        history = self._read_json(self.detection_history_file)
        
        detection_record = {
            "timestamp": datetime.now().isoformat(),
            "food": food_item,
            "confidence": round(confidence, 2),
            "calories": calories
        }
        
        history.append(detection_record)
        self._write_json(self.detection_history_file, history)
        
        # Update daily summary
        self._update_daily_summary(food_item, calories)
    
    def _update_daily_summary(self, food_item, calories):
        """Update daily calorie summary"""
        logs = self._read_json(self.calorie_logs_file)
        today = date.today().isoformat()
        
        if today not in logs:
            logs[today] = {
                "total_calories": 0,
                "foods": {},
                "detection_count": 0
            }
        
        # Update totals
        logs[today]["total_calories"] += calories
        logs[today]["detection_count"] += 1
        
        # Update food counts
        if food_item not in logs[today]["foods"]:
            logs[today]["foods"][food_item] = 0
        logs[today]["foods"][food_item] += 1
        
        self._write_json(self.calorie_logs_file, logs)
    
    def get_daily_summary(self, target_date=None):
        """
        Get daily calorie summary
        
        Args:
            target_date (str): Date in YYYY-MM-DD format, defaults to today
            
        Returns:
            dict: Daily summary data
        """
        if target_date is None:
            target_date = date.today().isoformat()
        
        logs = self._read_json(self.calorie_logs_file)
        return logs.get(target_date, {
            "total_calories": 0,
            "foods": {},
            "detection_count": 0
        })
    
    def get_recent_detections(self, limit=10):
        """
        Get recent detection history
        
        Args:
            limit (int): Number of recent detections to return
            
        Returns:
            list: Recent detection records
        """
        history = self._read_json(self.detection_history_file)
        return history[-limit:] if history else []
    
    def get_weekly_summary(self):
        """
        Get weekly calorie summary
        
        Returns:
            dict: Weekly summary data
        """
        logs = self._read_json(self.calorie_logs_file)
        
        # Get last 7 days
        from datetime import timedelta
        today = date.today()
        weekly_data = {}
        
        for i in range(7):
            day = today - timedelta(days=i)
            day_str = day.isoformat()
            weekly_data[day_str] = logs.get(day_str, {
                "total_calories": 0,
                "foods": {},
                "detection_count": 0
            })
        
        return weekly_data
    
    def get_all_time_stats(self):
        """
        Get all-time statistics
        
        Returns:
            dict: All-time stats
        """
        logs = self._read_json(self.calorie_logs_file)
        history = self._read_json(self.detection_history_file)
        
        total_calories = sum(day_data.get("total_calories", 0) for day_data in logs.values())
        total_detections = len(history)
        days_tracked = len(logs)
        
        # Most detected food
        food_counts = {}
        for detection in history:
            food = detection["food"]
            food_counts[food] = food_counts.get(food, 0) + 1
        
        most_detected_food = max(food_counts.items(), key=lambda x: x[1]) if food_counts else ("None", 0)
        
        return {
            "total_calories": total_calories,
            "total_detections": total_detections,
            "days_tracked": days_tracked,
            "avg_calories_per_day": round(total_calories / max(days_tracked, 1), 1),
            "most_detected_food": most_detected_food[0],
            "most_detected_count": most_detected_food[1]
        }
    
    def get_todays_detections(self):
        """
        Get all detections from today
        
        Returns:
            list: Today's detections
        """
        history = self._read_json(self.detection_history_file)
        today = datetime.now().date().isoformat()
        
        # Filter for today's detections
        todays_items = []
        for item in history:
            item_date = datetime.fromisoformat(item['timestamp']).date().isoformat()
            if item_date == today:
                todays_items.append(item)
        
        # Sort by timestamp (newest first)
        todays_items.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return todays_items
    
    def delete_detection(self, detection_id):
        """
        Delete a detection by its ID (timestamp)
        
        Args:
            detection_id (str): The timestamp ID of the detection to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        # Read current history
        history = self._read_json(self.detection_history_file)
        
        # Find the detection to delete
        detection_to_delete = None
        for detection in history:
            if detection['timestamp'] == detection_id:
                detection_to_delete = detection
                break
        
        if not detection_to_delete:
            return False
        
        # Remove from history
        history.remove(detection_to_delete)
        self._write_json(self.detection_history_file, history)
        
        # Update daily summary
        self._remove_from_daily_summary(detection_to_delete['food'], detection_to_delete['calories'])
        
        return True
    
    def _remove_from_daily_summary(self, food_item, calories):
        """Remove food item from daily summary"""
        logs = self._read_json(self.calorie_logs_file)
        today = date.today().isoformat()
        
        if today in logs:
            # Update totals
            logs[today]["total_calories"] -= calories
            logs[today]["detection_count"] -= 1
            
            # Update food counts
            if food_item in logs[today]["foods"]:
                logs[today]["foods"][food_item] -= 1
                if logs[today]["foods"][food_item] <= 0:
                    del logs[today]["foods"][food_item]
            
            self._write_json(self.calorie_logs_file, logs)