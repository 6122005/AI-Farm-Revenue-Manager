from typing import Dict, Any, List
from datetime import datetime

class SlotEngine:
    """
    Simplified Production Booking Slot Classification Engine.
    Strictly maps bookings to four base categories:
    - 12H Day
    - 12H Night
    - 24H Day
    - 24H Night
    """
    def __init__(self):
        self.slots = [
            {"code": "12H Day", "name": "12 Hour Day", "min_hours": 1.0, "max_hours": 13.0, "max_guests": 50, "is_active": True},
            {"code": "12H Night", "name": "12 Hour Night", "min_hours": 1.0, "max_hours": 13.0, "max_guests": 50, "is_active": True},
            {"code": "24H Day", "name": "24 Hour Day", "min_hours": 13.1, "max_hours": 24.0, "max_guests": 50, "is_active": True},
            {"code": "24H Night", "name": "24 Hour Night", "min_hours": 13.1, "max_hours": 24.0, "max_guests": 50, "is_active": True}
        ]
        self.slot_map = {s["code"]: s for s in self.slots}

    def get_slot_info(self, slot_code: str) -> Dict[str, Any]:
        normalized = self.normalize_commercial_slot(slot_code)
        return self.slot_map.get(normalized, {
            "code": normalized,
            "name": normalized,
            "min_hours": 12.0,
            "max_hours": 24.0,
            "max_guests": 50,
            "is_active": True
        })

    def normalize_commercial_slot(self, slot_val: Any) -> str:
        """
        Normalize slot names but preserve Couple categories.
        """
        s = str(slot_val).upper().strip().replace("_", " ").replace("-", " ")
        if "COUPLE" in s:
            if "NIGHT" in s:
                return "Couple Half Night"
            return "Couple Half Day"
            
        if "12H DAY" in s or "HALF DAY" in s:
            return "12H Day"
        elif "12H NIGHT" in s:
            return "12H Night"
        elif "24H DAY" in s:
            return "24H Day"
        elif "24H NIGHT" in s:
            return "24H Night"
            
        if "24H" in s or "EXTENDED" in s or "48H" in s or "MULTI" in s:
            if "NIGHT" in s:
                return "24H Night"
            return "24H Day"
        if "12H" in s:
            if "NIGHT" in s:
                return "12H Night"
            return "12H Day"
            
        # Fallbacks
        if "NIGHT" in s:
            return "12H Night"
        return "12H Day"

    def classify_booking(self, checkin_hour: int, duration_hours: float) -> str:
        """
        Simplification Rules:
        - Daytime start: 06:00 to 17:59
        - Nighttime start: 18:00 to 05:59
        """
        is_daytime = (6 <= checkin_hour < 18)

        if duration_hours <= 13:
            return "12H Day" if is_daytime else "12H Night"
        else:
            return "24H Day" if is_daytime else "24H Night"

    def classify_by_datetimes(self, start_dt_str: str, end_dt_str: str) -> Dict[str, Any]:
        """
        Classifies booking based on checkin hour and duration.
        Also returns whether it is an extended_stay (duration > 24).
        """
        try:
            start_dt = datetime.strptime(start_dt_str, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_dt_str, "%Y-%m-%d %H:%M")
            duration = max(1.0, (end_dt - start_dt).total_seconds() / 3600.0)
        except Exception:
            start_dt = datetime.now()
            duration = 12.0

        extended_stay = 1 if duration > 24 else 0
        slot_type = self.classify_booking(start_dt.hour, duration)

        return {
            "slot_type": slot_type,
            "extended_stay": extended_stay,
            "duration": duration
        }

    def classify_weekend(self, start_dt: datetime, slot: str) -> int:
        """
        Exact commercial weekend classification matching Farm_Booking_Data_new.xlsx formula.
        """
        if start_dt is None:
            return 0
            
        from datetime import time
        weekday = start_dt.weekday()
        start_time = start_dt.time()
        
        night_slots = {
            "12H Night",
            "Couple Half Night",
            "24H Night",
            "Couple Full Night",
        }
        day_slots = {
            "12H Day",
            "Couple Half Day",
            "24H Day",
            "Couple Full Day",
        }
        
        # Rule 1: Saturday (weekday=5) Evening/Night Booking >= 17:00
        if (
            weekday == 5
            and start_time >= time(17, 0)
            and slot in night_slots
        ):
            return 1
            
        # Rule 2: Sunday (weekday=6) Morning/Day Booking 06:00 to 11:59
        if (
            weekday == 6
            and time(6, 0) <= start_time < time(12, 0)
            and slot in day_slots
        ):
            return 1
            
        return 0

    def get_all_slots(self) -> List[Dict[str, Any]]:
        return self.slots

slot_engine = SlotEngine()
