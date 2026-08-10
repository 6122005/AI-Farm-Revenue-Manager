from app.services.prediction_engine import PredictionEngine
from app.services.data_pipeline import DataPipeline
from pathlib import Path
import json

# Process data first
print("Processing data...")
DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))

# Check group averages for 8 (August) 24H Night
with open("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/group_averages.json", "r") as f:
    avg_dict = json.load(f)
print("Weekend Base (seg_24H Night_8_1_mean):", avg_dict.get("seg_24H Night_8_1_mean", "Not Found"))

# Predict
engine = PredictionEngine()
req = {
    "start_datetime": "2026-08-08 19:00",
    "end_datetime": "2026-08-09 17:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 15
}
res = engine.predict(req)
print(f"August 2026 24H Night Weekend (10 guests, 15 lead days): ₹{res.recommended_price:,.0f}")
