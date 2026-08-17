import sys
from pathlib import Path
import pandas as pd

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.prediction_engine import prediction_engine
from app.services.feature_engineering import FeatureEngineer

# Compare 2026 vs 2023 rows
row_2026 = {
    "start_datetime": "2026-12-04 09:00",
    "booking_date": "2026-12-04",
    "commercial_slot": "12H Day",
    "slot_type": "12H Day",
    "person_count": 6,
    "lead_days": 0,
    "duration_hours": 7.0,
    "is_weekend": 0,
    "_is_prediction_row": True
}

row_2023 = {
    "start_datetime": "2023-12-04 09:00",
    "booking_date": "2023-12-04",
    "commercial_slot": "12H Day",
    "slot_type": "12H Day",
    "person_count": 6,
    "lead_days": 0,
    "duration_hours": 7.0,
    "is_weekend": 0,
    "_is_prediction_row": True
}

df_2026 = FeatureEngineer.process_dataframe(pd.DataFrame([row_2026]), is_prediction=True)
df_2023 = FeatureEngineer.process_dataframe(pd.DataFrame([row_2023]), is_prediction=True)

artifact = prediction_engine.model_artifact
feature_cols = artifact["features"]

print("--- DIFFERENCES IN MODEL FEATURES BETWEEN 2026 AND 2023 ---")
diff_found = False
for col in feature_cols:
    val_2026 = df_2026[col].iloc[0] if col in df_2026.columns else 0
    val_2023 = df_2023[col].iloc[0] if col in df_2023.columns else 0
    if val_2026 != val_2023:
        print(f"Feature '{col}': 2026 = {val_2026} | 2023 = {val_2023}")
        diff_found = True

if not diff_found:
    print("No feature differences found in feature_cols!")

print("\nModel Type:", artifact.get("model_type"))
