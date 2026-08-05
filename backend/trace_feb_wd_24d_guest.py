from app.services.guest_pricing_engine import guest_pricing_engine
rate, anchor = guest_pricing_engine.get_historical_guest_rate(
    requested_month=2,
    requested_slot="24H Day",
    requested_guests=10,
    requested_weekday_weekend=0 # Weekday
)
print(f"Guest Rate: {rate}, Anchor: {anchor}")
