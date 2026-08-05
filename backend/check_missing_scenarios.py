from app.services.prediction_engine import prediction_engine
import calendar
from datetime import datetime

year = 2026
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]

def get_sample_date(month, is_weekend):
    target_day = 5 if is_weekend else 1
    for day in range(1, 28):
        dt = datetime(year, month, day)
        if dt.weekday() == target_day:
            return dt.strftime("%Y-%m-%d 10:00")
    return None

missing_scenarios = []

for month in range(1, 13):
    month_name = calendar.month_name[month]
    for slot in slots:
        for is_weekend in [0, 1]:
            dt_str = get_sample_date(month, is_weekend)
            req = {
                "start_datetime": dt_str,
                "commercial_slot": slot,
                "person_count": 10,
                "lead_days": 10
            }
            try:
                res = prediction_engine.predict(req, is_batch=False)
                fallback_level = res.get("fallback_diagnostic", {}).get("level_used", "UNKNOWN")
                has_guest_rate = "historical_guest_rate" in res
                
                day_type = "Weekend" if is_weekend else "Weekday"
                
                # If it fell back to SAME_SEASON_SAME_SLOT or SAME_SLOT, it means it didn't find specific monthly records
                if fallback_level in ["SAME_SEASON_SAME_SLOT", "SAME_SLOT"]:
                    missing_scenarios.append({
                        "Month": month_name,
                        "Slot": slot,
                        "Day": day_type,
                        "Fallback": fallback_level,
                        "Guest_Rate_Found": has_guest_rate
                    })
            except Exception as e:
                print(f"Error on {month_name} {slot}: {e}")

if missing_scenarios:
    print("Scenarios where specific historical records (Same Month + Same Slot) were NOT found:")
    for s in missing_scenarios:
        print(f" - {s['Month']} | {s['Slot']} | {s['Day']} (Fallback used: {s['Fallback']}) | Guest Engine Match: {s['Guest_Rate_Found']}")
else:
    print("Awesome! Similar specific historical records were found for ALL 96 scenarios.")
