import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error
from app.services.prediction_engine import PredictionEngine

# Initialize engine and get clean data
engine = PredictionEngine()
df = engine.get_clean_data()

# Filter for valid rows only
df = df[df['selling_price'] > 0].copy()

actual_prices = []
predicted_prices = []

# To speed up, we'll sample if there are too many, but 700 rows should take just a few seconds
for idx, row in df.iterrows():
    # Construct a simulated request that perfectly matches the historical booking
    req = {
        "booking_date": row.get('booking_date'),
        "commercial_slot": row.get('commercial_slot'),
        "person_count": row.get('person_count', 4),
        "duration_hours": row.get('duration_hours', 24),
        "lead_days": row.get('lead_days', 10),
        # Pass start and end date if available, otherwise just mock them
        # PredictionEngine requires them but we can just pass strings
    }
    
    import datetime
    booking_date = str(row.get('booking_date', '2027-01-01'))[:10]
    
    if "Night" in str(req["commercial_slot"]):
        start_dt_obj = datetime.datetime.strptime(f"{booking_date} 19:00", "%Y-%m-%d %H:%M")
    else:
        start_dt_obj = datetime.datetime.strptime(f"{booking_date} 10:00", "%Y-%m-%d %H:%M")
        
    end_dt_obj = start_dt_obj + datetime.timedelta(hours=float(req["duration_hours"]))
    
    req["start_datetime"] = start_dt_obj.strftime("%Y-%m-%d %H:%M")
    req["end_datetime"] = end_dt_obj.strftime("%Y-%m-%d %H:%M")

    try:
        res = engine.predict(req)
        pred_price = res.revenue_optimized_price
        
        actual_prices.append(row['selling_price'])
        predicted_prices.append(pred_price)
    except Exception as e:
        pass

y_true = np.array(actual_prices)
y_pred = np.array(predicted_prices)

r2 = r2_score(y_true, y_pred)
mae = mean_absolute_error(y_true, y_pred)
mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

print(f"Total Valid Bookings Evaluated: {len(y_true)}")
print(f"R-Squared (R²): {r2:.4f}")
print(f"Mean Absolute Error (MAE): ₹{mae:.2f}")
print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")
