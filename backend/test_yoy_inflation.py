from app.services.prediction_engine import PredictionEngine
from app.services.data_pipeline import DataPipeline
from pathlib import Path
import json

print("1. Reprocessing Data Pipeline to calculate CMV and Time-Decay weights...")
DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))

with open("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/group_averages.json", "r") as f:
    avg_dict = json.load(f)

print(f"-> Global YoY Inflation Rate Calculated: {avg_dict.get('global_yoy_inflation', 0)*100:.2f}%")
print(f"-> Max Year in Data: {avg_dict.get('max_year_in_data', 0)}")
print(f"-> August 24H Night Weekend Base CMV: ₹{avg_dict.get('seg_24H Night_8_1_mean', 0):.0f}")

engine = PredictionEngine()

# Test 2026
req_2026 = {
    "start_datetime": "2026-08-08 19:00",
    "end_datetime": "2026-08-09 17:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 15
}
res_2026 = engine.predict(req_2026)

# Test 2027
req_2027 = {
    "start_datetime": "2027-08-07 19:00",
    "end_datetime": "2027-08-08 17:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 15
}
res_2027 = engine.predict(req_2027)

print("\n--- PREDICTION REPORT ---")
print(f"[August 2026] 24H Night Weekend (10 guests, 15 lead days): ₹{res_2026.recommended_price:,.0f}")
print(f"[August 2027] 24H Night Weekend (10 guests, 15 lead days): ₹{res_2027.recommended_price:,.0f}")
