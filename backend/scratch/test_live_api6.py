import asyncio
from app.api.predict import get_price_prediction
from app.models.schemas import PredictionRequest
from datetime import datetime, timedelta
from app.services.prediction_engine import prediction_engine
import pandas as pd

async def run():
    orig_predict = prediction_engine._predict_single_slot
    
    def debug_predict(features_dict, slot_type, artifact):
        # We need to trace the exact variables inside _predict_single_slot
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
                
        from app.services.historical_pricing_baseline import HistoricalPricingBaseline
        if "start_datetime" not in processed_df.columns:
            processed_df["start_datetime"] = pd.to_datetime(processed_df["booking_date"], errors="coerce")
            
        base_df = HistoricalPricingBaseline.fit_predict_expanding(processed_df)
        
        pred_row_base = base_df[base_df["_is_prediction_row"] == True]
        if not pred_row_base.empty:
            baseline_val = pred_row_base["historical_baseline_price"].iloc[0]
        else:
            baseline_val = base_df["selling_price"].median()
            
        model = artifact["model"]
        residual_val = float(model["base_model"].predict(X)[0])
        print(f"  --> DEBUG Baseline: {baseline_val}")
        print(f"  --> DEBUG Residual: {residual_val}")
        print(f"  --> DEBUG XGBoost vacation_weekend input: {X['vacation_weekend'].iloc[0]}")
        
        return orig_predict(features_dict, slot_type, artifact)
        
    prediction_engine._predict_single_slot = debug_predict

    print("Testing June 19, 2027 (Non-Vacation Saturday)")
    req1 = PredictionRequest(
        start_datetime="2027-06-19 19:00",
        end_datetime="2027-06-20 19:00",
        commercial_slot="24H Night",
        person_count=5,
        lead_days=3,
        booking_date="2027-06-16"
    )
    await get_price_prediction(req1)

    print("\nTesting June 5, 2027 (Vacation Saturday)")
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
