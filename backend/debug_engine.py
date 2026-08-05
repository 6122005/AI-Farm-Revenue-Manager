from app.services.guest_pricing_engine import HistoricalGuestPricingEngine

rate, closest = HistoricalGuestPricingEngine.get_historical_guest_rate(12, "24H Night", 10, 1)
print(f"Rate: {rate}, Closest: {closest}")
