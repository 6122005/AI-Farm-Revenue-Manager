from app.services.guest_pricing_engine import guest_pricing_engine

rate, anchor = guest_pricing_engine.get_historical_guest_rate(
    requested_month=2,
    requested_slot="24H Night",
    requested_guests=10,
    requested_weekday_weekend=1
)
print(f"Feb 24H Night Weekend: rate={rate}, anchor={anchor}")

rate, anchor = guest_pricing_engine.get_historical_guest_rate(
    requested_month=10,
    requested_slot="24H Night",
    requested_guests=10,
    requested_weekday_weekend=1
)
print(f"Oct 24H Night Weekend: rate={rate}, anchor={anchor}")
