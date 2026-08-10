import pandas as pd
import json
from pathlib import Path
from app.services.prediction_engine import PredictionEngine
from app.services.manual_festival_engine import ManualFestivalEngine

file_path = Path("data/Farm_Booking_Data_new.xlsx")

print("--- Sheet4 Content ---")
try:
    df = pd.read_excel(file_path, sheet_name="Sheet4")
    
    # Test Independence Day (2026-08-15) which has 1.2 multiplier
    fest_date_str = "2026-08-15"
    print(f"\nTargeting Future Festival on {fest_date_str}")
    
    engine = PredictionEngine()
    
    req = {
        "booking_date": fest_date_str,
        "commercial_slot": "24H Night",
        "person_count": 10,
        "duration_hours": 24,
        "lead_days": 5,
        "start_datetime": f"{fest_date_str} 19:00",
        "end_datetime": f"{fest_date_str} 19:00", 
        "skip_festival": False
    }
    
    res = engine.predict(req)
    
    print("\n--- Prediction Result ---")
    print(json.dumps(res.dict(), indent=2))
        
except Exception as e:
    print(f"Error: {e}")
