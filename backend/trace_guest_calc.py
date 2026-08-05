from app.services.guest_pricing_engine import guest_pricing_engine
from app.services.prediction_engine import prediction_engine
import numpy as np

req = {
    "start_datetime": "2026-02-07 10:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}

rate, closest_anchor = guest_pricing_engine.get_historical_guest_rate(
    requested_month=2,
    requested_slot="24H Night",
    requested_guests=10,
    requested_weekday_weekend=1 # Weekend
)

print(f"Rate: {rate}, Anchor: {closest_anchor}")

anchor_req = dict(req)
anchor_req["person_count"] = closest_anchor
anchor_req["skip_guest_engine"] = True

anchor_res = prediction_engine.predict(anchor_req, is_batch=True)
base_price = anchor_res.get("recommended_price", 0.0)

print(f"Base price for {closest_anchor} guests: {base_price}")

final_price = base_price + ((10 - closest_anchor) * rate)
rounded = float(np.round(final_price, -2))

print(f"Final price before rounding: {final_price}")
print(f"Final price after rounding: {rounded}")
