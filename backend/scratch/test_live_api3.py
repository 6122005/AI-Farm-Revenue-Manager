import asyncio
from app.api.predict import get_price_prediction
from app.models.schemas import PredictionRequest
from datetime import datetime, timedelta
from app.services.prediction_engine import prediction_engine
import joblib
from app.config import MODELS_DIR

async def run():
    orig_predict = prediction_engine._predict_single_slot
    
    def debug_predict(features_dict, slot_type, artifact):
        print(f"  -> Input dict: is_vacation={features_dict.get('is_vacation', 'Missing')}, is_weekend={features_dict.get('is_weekend', 'Missing')}")
        res = orig_predict(features_dict, slot_type, artifact)
        print(f"  -> Final predicted: {res}")
        return res
        
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
    res2 = await get_price_prediction(req2)
    print(f"Factors: {[f.factor for f in res2.price_factors]}")

asyncio.run(run())
