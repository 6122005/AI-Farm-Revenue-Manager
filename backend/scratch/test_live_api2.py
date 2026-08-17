import asyncio
from app.api.predict import get_price_prediction
from app.models.schemas import PredictionRequest
from datetime import datetime, timedelta
from app.services.prediction_engine import prediction_engine
import joblib
from app.config import MODELS_DIR

async def run():
    artifact = joblib.load(MODELS_DIR / "champion_model.joblib")
    features = artifact["features"]
    print(f"Is vacation_weekend in features? {'vacation_weekend' in features}")
    
    # We will temporarily patch the engine to print values
    orig_predict = prediction_engine._predict_single_slot
    
    def debug_predict(features_dict, slot_type, artifact):
        res = orig_predict(features_dict, slot_type, artifact)
        print(f"  -> ml_predicted: {res}")
        return res
        
    prediction_engine._predict_single_slot = debug_predict

    print("\nTesting June 19, 2027 (Non-Vacation Saturday)")
    req1 = PredictionRequest(
        start_datetime="2027-06-19 19:00",
        end_datetime="2027-06-20 19:00",
        commercial_slot="24H Night",
        person_count=5,
        lead_days=3,
        booking_date="2027-06-16"
    )
    res1 = await get_price_prediction(req1)

    print("\nTesting June 5, 2027 (Vacation Saturday)")
    req2 = PredictionRequest(
        start_datetime="2027-06-05 19:00",
        end_datetime="2027-06-06 19:00",
        commercial_slot="24H Night",
        person_count=5,
        lead_days=3,
        booking_date="2027-06-02"
    )
    res2 = await get_price_prediction(req2)

asyncio.run(run())
