from typing import Dict, Any, List
from datetime import datetime
from app.config import DEFAULT_COMMERCIAL_SLOTS

class SlotEngine:
    """
    Commercial Slot Engine.
    
    COMMERCIAL SLOTS:
    - COUPLE_SLOT: Couple Special (2 guests)
    - COUPLE_DAY: Couple Day (7 AM to 7 PM, 2 guests)
    - COUPLE_NIGHT: Couple Night (7 PM to 7 AM, 2 guests)
    - 12H_DAY: 12 Hour Day (7:00 AM to 7:00 PM)
    - 12H_NIGHT: 12 Hour Night (7:00 PM to 7:00 AM Next Day)
    - 24H_DAY: 24 Hour Day (7:00 AM to 7:00 AM Next Day)
    - 24H_NIGHT: 24 Hour Night (7:00 PM to 7:00 PM Next Day)
    """
    def __init__(self, slot_rules: List[Dict[str, Any]] = None):
        self.slots = slot_rules if slot_rules else DEFAULT_COMMERCIAL_SLOTS
        self.slot_map = {s["code"]: s for s in self.slots}

    def get_slot_info(self, slot_code: str) -> Dict[str, Any]:
        return self.slot_map.get(slot_code, {
            "code": slot_code,
            "name": slot_code,
            "min_hours": 12,
            "max_hours": 24,
            "max_guests": 50,
            "description": "Commercial Slot"
        })

    def map_request_to_slot(self, duration_hours: float, person_count: int = 4, is_night: bool = False) -> str:
        if person_count <= 2:
            return "COUPLE_NIGHT" if is_night else "COUPLE_DAY"
        
        if duration_hours <= 12:
            return "12H_NIGHT" if is_night else "12H_DAY"
        else:
            return "24H_NIGHT" if is_night else "24H_DAY"

    def map_duration_to_slot(self, duration_hours: float, person_count: int = 2) -> str:
        """Alias for backward compatibility."""
        return self.map_request_to_slot(duration_hours, person_count)

    def classify_by_datetimes(self, start_dt_str: str, end_dt_str: str, person_count: int = 4) -> str:
        """
        Classifies booking into commercial slot based on start & end datetimes and guest count.
        """
        try:
            start_dt = datetime.strptime(start_dt_str, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_dt_str, "%Y-%m-%d %H:%M")
            duration_hours = max(1.0, (end_dt - start_dt).total_seconds() / 3600.0)
            is_night = start_dt.hour >= 17 or start_dt.hour < 5
            return self.map_request_to_slot(duration_hours, person_count, is_night)
        except Exception:
            return "12H_DAY" if person_count > 2 else "COUPLE_DAY"

    def get_all_slots(self) -> List[Dict[str, Any]]:
        return self.slots

slot_engine = SlotEngine()
