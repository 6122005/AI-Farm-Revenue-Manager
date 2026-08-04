from app.services.prediction_engine import prediction_engine
from datetime import date, timedelta
tomorrow = date.today() + timedelta(days=1)
req_couple = {
    "booking_date": str(tomorrow),
    "commercial_slot": "Couple Full Day",
    "person_count": 10,
    "duration_hours": 12,
    "lead_days": 1
}

# Override the prediction engine locally to catch the traceback
import traceback

original_predict = prediction_engine.predict
def my_predict(*args, **kwargs):
    try:
        return original_predict(*args, **kwargs)
    except Exception as e:
        traceback.print_exc()
        raise e

prediction_engine.predict = my_predict

res_c10 = prediction_engine.predict(req_couple)
print(f"Couple 10 pax: {res_c10['recommended_price']}")
