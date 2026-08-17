import asyncio
from app.api.predict import get_price_prediction
from app.models.schemas import PredictionRequest
from app.services.prediction_engine import prediction_engine
import pandas as pd

async def run():
    orig_predict = prediction_engine._predict_single_slot
    
    def debug_predict(features_dict, slot_type, artifact):
        pred_df = pd.DataFrame([features_dict])
        pred_df["_is_prediction_row"] = True
        from app.services.feature_engineering import FeatureEngineer
        processed_pred_df = FeatureEngineer.process_dataframe(pred_df, is_prediction=True)
        
        hist_df = prediction_engine.get_clean_data()
        processed_df = pd.concat([hist_df, processed_pred_df], ignore_index=True)
        df = processed_pred_df.copy()
        
        from app.services.slot_relationship_engine import slot_engine
        df["slot_norm"] = slot_engine.normalize_commercial_slot(slot_type)
        
        feature_cols = artifact["features"]
        cat_cols = artifact.get("categorical_features", [])
        
        for col in feature_cols:
            if col not in df.columns:
                if col == "slot_norm":
                    df[col] = slot_engine.normalize_commercial_slot(slot_type)
                elif col in ["highest_revenue_weekday", "highest_revenue_month", "weekend_premium_ratio"]:
                    df[col] = 1.0
                elif col in cat_cols:
                    df[col] = "Unknown"
                else:
                    df[col] = 0.0
                    
        if "is_vacation" in df.columns and "is_weekend" in df.columns:
            df["vacation_weekend"] = df["is_vacation"] * df["is_weekend"]
        else:
            df["vacation_weekend"] = 0

        X = df[feature_cols].copy()
        
        for col in cat_cols:
            if col in X.columns:
                X[col] = X[col].astype('category')
                
        for col in X.columns:
            if col not in cat_cols:
                X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
                
        # PRINT TOP 10 IMPORTANT FEATURES TO SEE IF THEY MATCH TRAINING
        print(f"DEBUG X values: vacation_weekend={X['vacation_weekend'].iloc[0]}, person_count={X['person_count'].iloc[0]}, lead_days={X['lead_days'].iloc[0]}, duration={X['duration'].iloc[0]}, month={X['month'].iloc[0]}")
        
        return orig_predict(features_dict, slot_type, artifact)
        
    prediction_engine._predict_single_slot = debug_predict

    print("Testing June 5, 2027 (Vacation Saturday)")
    req2 = PredictionRequest(
        start_datetime="2027-06-05 19:00",
        end_datetime="2027-06-06 19:00",
        commercial_slot="24H Night",
        person_count=5,
        lead_days=3,
        booking_date="2027-06-02"
    )
    await get_price_prediction(req2)

asyncio.run(run())
