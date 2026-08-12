from app.services.prediction_engine import prediction_engine
req = {
    "start_datetime": "2026-08-20 19:00",
    "duration_hours": 24,
    "person_count": 2,
    "lead_days": 8,
    "booking_notes": ""
}
try:
    prediction_engine.reload_model()
    res = prediction_engine.predict(req)
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
