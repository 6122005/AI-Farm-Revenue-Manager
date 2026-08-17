from datetime import datetime
import pandas as pd

class BusinessCalendar:
    
    SUPPORTED_SUNDAY_CATEGORIES = [
        "24H DAY", "12H DAY", "12H NIGHT", "24H NIGHT", 
        "COUPLE HALF DAY", "COUPLE FULL DAY", "COUPLE HALF NIGHT", "COUPLE FULL NIGHT"
    ]
    
    SATURDAY_NIGHT_CATEGORIES = [
        "12H NIGHT", "24H NIGHT", "COUPLE HALF NIGHT", "COUPLE FULL NIGHT"
    ]

    @classmethod
    def calculate_business_weekend(cls, start_datetime, booking_category: str) -> dict:
        """
        Calculates exact farm business weekend logic based on explicit category and datetime matching.
        """
        if pd.isna(start_datetime) or start_datetime is None:
            return {
                "calendar_day_of_week": -1,
                "calendar_is_saturday": 0,
                "calendar_is_sunday": 0,
                "business_is_weekend": 0,
                "business_weekend_reason": "INVALID_DATETIME"
            }
            
        if not isinstance(start_datetime, datetime):
            try:
                start_datetime = pd.to_datetime(start_datetime)
            except Exception:
                return {
                    "calendar_day_of_week": -1,
                    "calendar_is_saturday": 0,
                    "calendar_is_sunday": 0,
                    "business_is_weekend": 0,
                    "business_weekend_reason": "INVALID_DATETIME"
                }
                
        day_of_week = start_datetime.weekday()
        hour = start_datetime.hour
        
        result = {
            "calendar_day_of_week": day_of_week,
            "calendar_is_saturday": 1 if day_of_week == 5 else 0,
            "calendar_is_sunday": 1 if day_of_week == 6 else 0,
            "business_is_weekend": 0,
            "business_weekend_reason": ""
        }
        
        cat_upper = str(booking_category).upper() if booking_category else "UNKNOWN"
        
        if day_of_week == 5:
            # 5. Saturday AFTER 17:00:00 PM is WEEKEND
            if hour >= 17:
                result["business_is_weekend"] = 1
                result["business_weekend_reason"] = "SATURDAY_AFTER_17_WEEKEND"
            else:
                result["business_is_weekend"] = 0
                result["business_weekend_reason"] = "SATURDAY_BEFORE_17_WEEKDAY"
            
        elif day_of_week == 6:
            # 6. Entire Sunday (all day & night) is WEEKEND
            result["business_is_weekend"] = 1
            result["business_weekend_reason"] = "ENTIRE_SUNDAY_WEEKEND"
                
        else:
            # Mon-Fri
            result["business_is_weekend"] = 0
            result["business_weekend_reason"] = "WEEKDAY"
            
        return result
