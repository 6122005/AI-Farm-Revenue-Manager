import sys
from pathlib import Path
import pandas as pd

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.prediction_engine import prediction_engine

# 1. 2026-12-04 09:00
req_2026 = {
    "start_datetime": "2026-12-04 09:00",
    "end_datetime": "2026-12-04 16:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0
}
res_2026 = prediction_engine.predict(req_2026)
print("=== 2026-12-04 RESULT ===")
print("Recommended Price:", res_2026.recommended_price)
print("Raw Model Price:", res_2026.raw_model_price)
print("Factors:", res_2026.price_factors)

print("\n" + "="*40 + "\n")

# 2. 2023-12-04 09:00
req_2023 = {
    "start_datetime": "2023-12-04 09:00",
    "end_datetime": "2023-12-04 16:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0
}
res_2023 = prediction_engine.predict(req_2023)
print("=== 2023-12-04 RESULT ===")
print("Recommended Price:", res_2023.recommended_price)
print("Raw Model Price:", res_2023.raw_model_price)
print("Factors:", res_2023.price_factors)

print("\n" + "="*40 + "\n")

# 3. 2023-12-04 09:00 with exclude_index=2 (as done in CSV evaluation)
req_2023_ex = {
    "start_datetime": "2023-12-04 09:00",
    "end_datetime": "2023-12-04 16:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0,
    "exclude_index": 2
}
res_2023_ex = prediction_engine.predict(req_2023_ex)
print("=== 2023-12-04 WITH EXCLUDE_INDEX RESULT ===")
print("Recommended Price:", res_2023_ex.recommended_price)
print("Raw Model Price:", res_2023_ex.raw_model_price)
