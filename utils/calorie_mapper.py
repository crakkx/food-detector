"""
Food to Calorie Mapping Module
Maps detected food items to their approximate calorie values
"""

class CalorieMapper:
    def __init__(self):
        # Calorie mapping for detected food items (per average serving)
        self.calorie_map = {
            "Apple": 95,        # 1 medium apple
            "Orange": 85,       # 1 medium orange  
            "Banana": 105,      # 1 medium banana
            "Strawberry": 50,   # 1 cup strawberries
            "Cucumber": 16,     # 1 cup sliced cucumber
            "Pizza": 285,       # 1 slice pizza
            "Watermelon": 46,   # 1 cup watermelon
            "Bread": 80,        # 1 slice bread
            "Broccoli": 25,     # 1 cup broccoli
            "Carrot": 25        # 1 medium carrot
        }
        
        # Food category mapping for nutritional info
        self.food_categories = {
            "Apple": "Fruit",
            "Orange": "Fruit", 
            "Banana": "Fruit",
            "Strawberry": "Fruit",
            "Cucumber": "Vegetable",
            "Pizza": "Fast Food",
            "Watermelon": "Fruit",
            "Bread": "Grain",
            "Broccoli": "Vegetable",
            "Carrot": "Vegetable"
        }
    
    def get_calories(self, food_item):
        """
        Get calorie count for a detected food item
        
        Args:
            food_item (str): Name of the detected food
            
        Returns:
            int: Calorie count for the food item
        """
        return self.calorie_map.get(food_item, 0)
    
    def get_category(self, food_item):
        """
        Get food category for a detected food item
        
        Args:
            food_item (str): Name of the detected food
            
        Returns:
            str: Category of the food item
        """
        return self.food_categories.get(food_item, "Unknown")
    
    def get_all_foods(self):
        """
        Get all available foods and their calories
        
        Returns:
            dict: All foods with their calorie values
        """
        return self.calorie_map.copy()
    
    def calculate_total_calories(self, food_detections):
        """
        Calculate total calories from a list of detected foods
        
        Args:
            food_detections (list): List of detected food items
            
        Returns:
            int: Total calorie count
        """
        total = 0
        for food in food_detections:
            total += self.get_calories(food)
        return total
    
    def get_nutritional_summary(self, food_detections):
        """
        Get nutritional summary by category
        
        Args:
            food_detections (list): List of detected food items
            
        Returns:
            dict: Summary by food category
        """
        summary = {}
        for food in food_detections:
            category = self.get_category(food)
            calories = self.get_calories(food)
            
            if category not in summary:
                summary[category] = {"count": 0, "calories": 0, "foods": []}
            
            summary[category]["count"] += 1
            summary[category]["calories"] += calories
            summary[category]["foods"].append(food)
        
        return summary