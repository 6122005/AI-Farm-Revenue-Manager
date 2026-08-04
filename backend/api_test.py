from app.services.prediction_engine import prediction_engine
from datetime import date, timedelta

tomorrow = date.today() + timedelta(days=1)
day_20 = date.today() + timedelta(days=20)
day_35 = date.today() + timedelta(days=35)
day_50 = date.today() + timedelta(days=50)

print("=== 1. TESTING LEAD DAYS PREMIUM (12H Day, 4 Guests) ===")
def get_price(b_date, lead):
    req = {
        "booking_date": str(b_date),
        "commercial_slot": "12H Day",
        "person_count": 4,
        "duration_hours": 12,
        "lead_days": lead
    }
    res = prediction_engine.predict(req)
    return res.get("recommended_price")

print(f"Lead ~1 Day (Tomorrow): ₹{get_price(tomorrow, 1)}")
print(f"Lead ~20 Days: ₹{get_price(day_20, 20)} (Expected +₹100)")
print(f"Lead ~35 Days: ₹{get_price(day_35, 35)} (Expected +₹200)")
print(f"Lead ~50 Days: ₹{get_price(day_50, 50)} (Expected +₹300)")
print("")

print("=== 2. TESTING COUPLE SLOT GUEST COUNT (Couple Full Day) ===")
def get_couple_price(guests):
    req = {
        "booking_date": str(tomorrow),
        "commercial_slot": "Couple Full Day",
        "person_count": guests,
        "duration_hours": 12,
        "lead_days": 1
    }
    res = prediction_engine.predict(req)
    return res.get("recommended_price")

print(f"Couple Slot for 4 Guests: ₹{get_couple_price(4)}")
print(f"Couple Slot for 10 Guests: ₹{get_couple_price(10)}")
