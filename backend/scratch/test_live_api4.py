import asyncio
from app.api.predict import get_price_prediction
from app.models.schemas import PredictionRequest
from datetime import datetime, timedelta
from app.services.prediction_engine import prediction_engine
import pandas as pd

async def run():
    # We will temporarily patch prediction engine to print values INSIDE _predict_single_slot
    orig_predict = prediction_engine._predict_single_slot
    
    def debug_predict(features_dict, slot_type, artifact):
        # We need to trace the exact variables inside _predict_single_slot
        # So we will replicate the logic here temporarily to print them
        
        pred_df = pd.DataFrame([features_dict])
        pred_df["_is_prediction_row"] = True
        from app.services.feature_engineering import FeatureEngineer
        processed_pred_df = FeatureEngineer.process_dataframe(pred_df, is_prediction=True)
        
        print(f"  -> DF is_vacation: {processed_pred_df.get('is_vacation', pd.Series([None])).iloc[0]}")
        print(f"  -> DF is_weekend: {processed_pred_df.get('is_weekend', pd.Series([None])).iloc[0]}")
        
        res = orig_predict(features_dict, slot_type, artifact)
        print(f"  -> Final predicted: {res}")
        return res
        
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
