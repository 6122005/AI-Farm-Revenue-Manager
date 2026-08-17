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
        res = orig_predict(features_dict, slot_type, artifact)
        
        # We will directly monkey patch prediction_engine to see what happens inside
        
        return res
        
    prediction_engine._predict_single_slot = debug_predict

    # Let's directly modify prediction_engine to print values before it returns
    with open("app/services/prediction_engine.py", "r") as f:
        code = f.read()
    
    # We will temporarily print baseline_val and residual_val
    if "print(f'  DEBUG: baseline={baseline_val}, residual={residual_val}')" not in code:
        code = code.replace("residual_val = float(model[\"base_model\"].predict(X)[0])",
                            "residual_val = float(model[\"base_model\"].predict(X)[0])\n            print(f'  DEBUG: baseline={baseline_val}, residual={residual_val}')")
        with open("app/services/prediction_engine.py", "w") as f:
            f.write(code)

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
