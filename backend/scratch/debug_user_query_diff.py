import sys
from pathlib import Path
import pandas as pd

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.prediction_engine import prediction_engine

# 1. User UI query
req_ui = {
    "start_datetime": "2026-12-04 19:00",
    "end_datetime": "2026-12-05 14:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0,
    "competitor_price": 0
}
res_ui = prediction_engine.predict(req_ui)
print("--- USER UI QUERY RESULT ---")
print("Recommended Price:", res_ui.recommended_price)
print("Raw Model Price:", res_ui.raw_model_price)
print("Factors:", res_ui.price_factors)

print("\n-----------------------------------\n")

# 2. Excel row #3 query (2023-12-04 09:00)
req_excel = {
    "start_datetime": "2023-12-04 09:00",
    "end_datetime": "2023-12-04 16:00",
    "commercial_slot": "12H Day",
    "person_count": 6,
    "lead_days": 0,
    "competitor_price": 0
}
res_excel = prediction_engine.predict(req_excel)
print("--- EXCEL ROW #3 QUERY RESULT ---")
print("Recommended Price:", res_excel.recommended_price)
print("Raw Model Price:", res_excel.raw_model_price)
print("Factors:", res_excel.price_factors)
