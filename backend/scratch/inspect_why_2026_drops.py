import sys
from pathlib import Path
import pandas as pd
import numpy as np

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.prediction_engine import prediction_engine
from app.services.feature_engineering import FeatureEngineer
from app.services.historical_pricing_baseline import HistoricalPricingBaseline

row_2026 = {
    "start_datetime": "2026-12-04 09:00",
    "end_datetime": "2026-12-04 16:00",
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
    "end_datetime": "2023-12-04 16:00",
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
cat_cols = artifact.get("categorical_features", [])

def prep_X(df):
    d = df.copy()
    for col in feature_cols:
        if col not in d.columns:
            if col in cat_cols:
                d[col] = "Unknown"
            else:
                d[col] = 0.0
    X = d[feature_cols].copy()
    for col in cat_cols:
        if col in X.columns:
            X[col] = X[col].astype('category')
    for col in X.columns:
        if col not in cat_cols:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
    return X

X_2026 = prep_X(df_2026)
X_2023 = prep_X(df_2023)

model = artifact["model"]
base_model = model["base_model"]

res_2026 = base_model.predict(X_2026)[0]
res_2023 = base_model.predict(X_2023)[0]
print(f"XGBoost Model Residual 2026: {res_2026:.2f}")
print(f"XGBoost Model Residual 2023: {res_2023:.2f}")

# Now check baseline lookup!
df_clean = prediction_engine.get_clean_data()
df_comb_2026 = pd.concat([df_clean, df_2026], ignore_index=True)
df_comb_2023 = pd.concat([df_clean, df_2023], ignore_index=True)

base_df_2026 = HistoricalPricingBaseline.fit_predict_expanding(df_comb_2026)
base_df_2023 = HistoricalPricingBaseline.fit_predict_expanding(df_comb_2023)

r26 = base_df_2026[base_df_2026["_is_prediction_row"] == True]
r23 = base_df_2023[base_df_2023["_is_prediction_row"] == True]

b26 = r26["historical_baseline_price"].iloc[0]
b23 = r23["historical_baseline_price"].iloc[0]

l26 = r26["matched_level"].iloc[0] if "matched_level" in r26.columns else "N/A"
l23 = r23["matched_level"].iloc[0] if "matched_level" in r23.columns else "N/A"

print(f"Baseline Price 2026: {b26} (Level {l26})")
print(f"Baseline Price 2023: {b23} (Level {l23})")

print(f"\nTOTAL PREDICTED 2026: {b26 + res_2026:.2f}")
print(f"TOTAL PREDICTED 2023: {b23 + res_2023:.2f}")
