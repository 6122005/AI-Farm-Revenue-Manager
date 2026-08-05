import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.prediction_engine import prediction_engine
import xgboost as xgb

def run_forensic_audit():
    print("Starting Forensic Audit...")
    
    # 1. Load Training Data & Pipeline
    df_raw = DataPipeline.process_with_explicit_mapping(
        file_path=Path("data/Farm_Booking_Data.xlsx"),
        date_col="booking_date",
        slot_col="commercial_slot",
        price_col="selling_price",
        guests_col="person_count",
        lead_col="lead_days",
        competitor_col="competitor_price"
    )
    df_raw = df_raw.sort_values(by="booking_date").reset_index(drop=True)
    
    # Generate Offline Training Features (identical to train_script.py)
    df_offline = FeatureEngineer.process_dataframe(df_raw.copy(), is_prediction=False)
    
    # Load Model Metadata
    metadata_path = Path("models_store/champion_metadata.json")
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
        
    expected_features = metadata.get("features", [])
    champion_name = metadata.get("champion_model", "XGBoost")
    
    print(f"Model Champion: {champion_name}, Expected Features: {len(expected_features)}")
    
    # Sample 30 bookings for comparison
    np.random.seed(42)
    sample_indices = np.random.choice(len(df_raw), 30, replace=False)
    
    feature_diffs = []
    prediction_diffs = []
    
    model = joblib.load("models_store/champion_model.joblib")
    
    for idx in sample_indices:
        row_raw = df_raw.iloc[idx]
        row_offline = df_offline.iloc[idx]
        
        b_date = row_raw["booking_date"].strftime("%Y-%m-%d") if isinstance(row_raw["booking_date"], pd.Timestamp) else str(row_raw["booking_date"])
        
        # 1. OFFLINE PREDICTION
        offline_vector = row_offline.reindex(expected_features, fill_value=0).values.reshape(1, -1)
        offline_pred = float(model["model"].predict(offline_vector)[0])
        actual_price = float(row_raw["selling_price"])
        
        # 2. ONLINE INFERENCE (PredictionEngine)
        req = {
            "start_datetime": f"{b_date} 10:00",
            "end_datetime": f"{b_date} 22:00",
            "booking_date": b_date,
            "commercial_slot": row_raw["commercial_slot"],
            "person_count": int(row_raw["person_count"]),
            "lead_days": int(row_raw.get("lead_days", 7)),
            "competitor_price": 0.0,
            "skip_consistency_check": False
        }
        
        # Step-by-step trace of PredictionEngine to get inference features
        # We need to simulate exactly what prediction_engine does
        df_req = pd.DataFrame([req])
        df_req['month'] = int(b_date.split("-")[1])
        day_of_week = pd.to_datetime(b_date).dayofweek
        df_req['is_weekend'] = day_of_week >= 5
        df_req['commercial_slot'] = req['commercial_slot']
        df_req['person_count'] = req['person_count']
        df_req['lead_days'] = req['lead_days']
        df_req['competitor_price'] = req['competitor_price']
        
        # In predict(), it does: df_infer = FeatureEngineer.process_dataframe(df_req, is_prediction=True)
        # WAIT! In PredictionEngine.predict(), does it pass historical_df??? Let's check!
        df_infer = FeatureEngineer.process_dataframe(df_req, is_prediction=True, historical_df=df_raw.copy())
        
        # Align features
        for f in expected_features:
            if f not in df_infer.columns:
                df_infer[f] = 0
        df_infer = df_infer[expected_features]
        online_vector = df_infer.iloc[0].values.reshape(1, -1)
        
        # Online ML Prediction natively
        res = prediction_engine.predict(req)
        online_pred = res.shadow_ml_price
        
        prediction_diffs.append({
            "Booking_Date": b_date,
            "Slot": row_raw["commercial_slot"],
            "Actual_Price": actual_price,
            "Offline_Pred": offline_pred,
            "Online_Pred": online_pred,
            "Offline_Error": abs(actual_price - offline_pred),
            "Online_Error": abs(actual_price - online_pred),
            "Diff_Preds": abs(offline_pred - online_pred)
        })
        
        # Feature Comparison
        for f in expected_features:
            val_off = row_offline.get(f, 0)
            val_on = df_infer.iloc[0].get(f, 0)
            if pd.isna(val_off): val_off = 0
            if pd.isna(val_on): val_on = 0
            
            # Allow minor float precision differences
            if isinstance(val_off, float) and isinstance(val_on, float):
                is_diff = abs(val_off - val_on) > 0.001
            else:
                is_diff = str(val_off) != str(val_on)
                
            if is_diff:
                feature_diffs.append({
                    "Booking_Date": b_date,
                    "Feature": f,
                    "Offline_Value": val_off,
                    "Online_Value": val_on
                })
                
    pd.DataFrame(prediction_diffs).to_csv("prediction_diff.csv", index=False)
    pd.DataFrame(feature_diffs).to_csv("feature_diff.csv", index=False)
    
    print("Finished trace. Check prediction_diff.csv and feature_diff.csv")
    
if __name__ == "__main__":
    run_forensic_audit()
