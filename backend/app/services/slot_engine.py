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
        Normalize slot names preserving Couple and 24H variants.
        """
        s = str(slot_val).upper().strip().replace("_", " ").replace("-", " ")
        if "COUPLE" in s:
            if "NIGHT" in s:
                return "Couple Half Night"
            return "Couple Half Day"
            
        is_24 = any(k in s for k in ["24H", "24 HOUR", "24 HRS", "FULL DAY", "FULL NIGHT", "48H", "EXTENDED", "MULTI"])
        is_night = any(k in s for k in ["NIGHT", "19:00", "20:00", "21:00", "22:00"])
        
        if is_24:
            if is_night:
                return "24H Night"
            return "24H Day"
            
        if "12H DAY" in s or "HALF DAY" in s or "DAY" in s:
            if "NIGHT" not in s:
                return "12H Day"
                
        if "12H NIGHT" in s or "HALF NIGHT" in s or "NIGHT" in s:
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

    def classify_weekend(self, start_dt: datetime, slot: str = "") -> int:
        """
        User Explicit Weekend Directive:
        - Saturday AFTER 17:00:00 PM -> WEEKEND (1)
        - Entire Sunday (all day & night) -> WEEKEND (1)
        - All other times (Mon-Fri, and Saturday before 17:00:00 PM) -> WEEKDAY (0)
        """
        if start_dt is None:
            return 0
            
        weekday = start_dt.weekday() # 0=Mon, 4=Fri, 5=Sat, 6=Sun
        hour = start_dt.hour
        
        # Rule 1: Saturday (weekday=5) AFTER 17:00:00 PM
        if weekday == 5:
            if hour >= 17:
                return 1
            return 0
            
        # Rule 2: Entire Sunday (weekday=6)
        if weekday == 6:
            return 1
            
        return 0

    def get_all_slots(self) -> List[Dict[str, Any]]:
        return self.slots

slot_engine = SlotEngine()
