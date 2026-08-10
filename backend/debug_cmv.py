from app.services.prediction_engine import PredictionEngine
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

engine = PredictionEngine()
engine.predict({"start_datetime": "2026-11-04 19:00", "end_datetime": "2026-11-05 19:00", "commercial_slot": "24H Night", "person_count": 10})
df = engine._clean_data_cache
row = df[df['booking_date'] == "2024-11-03"].iloc[0]

marginal_cost = row.get('marginal_cost', 50.0) # approx
extra_guests = max(0, row['person_count'] - 4)

print("selling_price:", row['selling_price'])
print("person_count:", row['person_count'])
print("duration_hours:", row['duration_hours'])
print("extra_guests:", extra_guests)
print("cmv_base_price from cache:", row['cmv_base_price'])

# Recalculate
# norm_selling_price for 24 hours is just selling_price
norm_selling_price = row['selling_price']
base_selling_price = norm_selling_price - extra_guests * marginal_cost
print("recalculated base_selling_price (assuming 50/guest):", base_selling_price)
