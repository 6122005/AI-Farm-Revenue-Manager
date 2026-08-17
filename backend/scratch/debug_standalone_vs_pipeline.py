import sys
from pathlib import Path
import pandas as pd

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.prediction_engine import prediction_engine
from app.services.data_pipeline import DataPipeline

excel_path = backend_dir / "data" / "Farm_Booking_Data_new.xlsx"
df_clean = DataPipeline.load_and_process_file(excel_path)

# Find row #3 in df_clean (2023-12-04 09:00)
row3 = df_clean.iloc[2]
print("Row #3 from df_clean:")
print("booking_date:", row3.get("booking_date"))
print("start_datetime:", row3.get("start_datetime"))
print("commercial_slot:", row3.get("commercial_slot"))
print("duration_hours:", row3.get("duration_hours"))
print("selling_price:", row3.get("selling_price"))

# Query standalone via predict()
req_2023_04 = {
    "start_datetime": "2023-12-04 09:00",
    "end_datetime": "2023-12-04 16:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0
}
res = prediction_engine.predict(req_2023_04)
print("\nPredict() result for 2023-12-04 09:00:")
print("Recommended price:", res.recommended_price)
print("Raw model price:", res.raw_model_price)

# Query standalone via predict() for 2026-12-04 09:00
req_2026_04 = {
    "start_datetime": "2026-12-04 09:00",
    "end_datetime": "2026-12-04 16:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0
}
res_2026 = prediction_engine.predict(req_2026_04)
print("\nPredict() result for 2026-12-04 09:00:")
print("Recommended price:", res_2026.recommended_price)
print("Raw model price:", res_2026.raw_model_price)
