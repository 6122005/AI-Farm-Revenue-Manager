from app.services.guest_pricing_engine import guest_pricing_engine

months = [7, 8, 9, 10, 11, 2]
print(f"{'Month':<8} | {'Rate':<8} | {'Anchor':<8}")
print("-" * 30)

for m in months:
    rate, anchor = guest_pricing_engine.get_historical_guest_rate(
        requested_month=m,
        requested_slot="24H Night",
        requested_guests=10,
        requested_weekday_weekend=1 # Weekend
    )
    print(f"{m:<8} | {str(rate):<8} | {str(anchor):<8}")
