import asyncio
from app.api.predict import get_price_prediction
from app.models.schemas import PredictionRequest
from datetime import datetime, timedelta

async def run():
    print("Testing June 19, 2027 (Non-Vacation Saturday)")
    req1 = PredictionRequest(
        start_datetime="2027-06-19 19:00",
        end_datetime="2027-06-20 19:00",
        commercial_slot="24H Night",
        person_count=5,
        lead_days=3,
        booking_date="2027-06-16"
    )
    res1 = await get_price_prediction(req1)
    print(f"Non-Vacation Price: ₹{res1.recommended_price}")

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
    print(f"Vacation Price: ₹{res2.recommended_price}")

asyncio.run(run())
