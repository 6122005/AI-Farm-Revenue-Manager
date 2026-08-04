from app.services.prediction_engine import prediction_engine
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
day_20 = date.today() + timedelta(days=20)
day_35 = date.today() + timedelta(days=35)
day_50 = date.today() + timedelta(days=50)

# Lead Days test
req_base = {
    "booking_date": str(tomorrow),
    "commercial_slot": "12H Day",
    "person_count": 4,
    "duration_hours": 12,
    "lead_days": 1
}

res_base = prediction_engine.predict(req_base)
req_base["booking_date"] = str(day_20)
req_base["lead_days"] = 20
res_20 = prediction_engine.predict(req_base)
req_base["booking_date"] = str(day_35)
req_base["lead_days"] = 35
res_35 = prediction_engine.predict(req_base)
req_base["booking_date"] = str(day_50)
req_base["lead_days"] = 50
res_50 = prediction_engine.predict(req_base)

print(f"Lead 1: {res_base['recommended_price']}")
print(f"Lead 20: {res_20['recommended_price']}")
print(f"Lead 35: {res_35['recommended_price']}")
print(f"Lead 50: {res_50['recommended_price']}")

# Couple slot test
req_couple = {
    "booking_date": str(tomorrow),
    "commercial_slot": "Couple Full Day",
    "person_count": 4,
    "duration_hours": 12,
    "lead_days": 1
}
res_c4 = prediction_engine.predict(req_couple)
req_couple["person_count"] = 10
res_c10 = prediction_engine.predict(req_couple)
print(f"Couple 4 pax: {res_c4['recommended_price']}")
print(f"Couple 10 pax: {res_c10['recommended_price']}")

# Normal slot big pax test
req_norm = {
    "booking_date": str(tomorrow),
    "commercial_slot": "12H Day",
    "person_count": 4,
    "duration_hours": 12,
    "lead_days": 1
}
res_n4 = prediction_engine.predict(req_norm)
req_norm["person_count"] = 10
res_n10 = prediction_engine.predict(req_norm)
print(f"Normal 4 pax: {res_n4['recommended_price']}")
print(f"Normal 10 pax: {res_n10['recommended_price']}")

