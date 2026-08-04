import pandas as pd
from app.services.prediction_engine import prediction_engine
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error

df = pd.read_csv('data/clean_booking_data.csv')

filtered_df = df[
    (df['is_festival'] == 0) & 
    (df['selling_price'] >= 500) &
    (~df['festival_name'].astype(str).str.lower().str.strip().isin(['makar sankranti', 'holi', 'dhuleti']))
].copy()

results = []
count = 0
total = len(filtered_df)

y_true = []
y_pred = []

print(f"Total valid historical records to test: {total}")

for idx, row in filtered_df.iterrows():
    try:
        req = {
            "start_datetime": f"{row['booking_date']} 10:00",
            "slot_type": row['commercial_slot'],
            "commercial_slot": row['commercial_slot'],
            "person_count": int(row['person_count']),
            "lead_days": float(row.get('lead_days', 10)),
        }
        
        res = prediction_engine.predict(req, is_batch=True)
        pred_price = res.get('recommended_price', 0)
        actual_price = row['selling_price']
        
        y_true.append(actual_price)
        y_pred.append(pred_price)
        
    except Exception as e:
        print(f"Error on {row['booking_date']}: {e}")
        
    count += 1
    if count % 100 == 0:
        print(f"Processed {count}/{total}")

if len(y_true) > 0:
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    print(f"\n--- Metrics on Filtered Dataset ---")
    print(f"Total Records Tested: {len(y_true)}")
    print(f"R-squared (R²): {r2:.4f}")
    print(f"Mean Absolute Error (MAE): ₹{mae:,.2f}")
else:
    print("No records processed successfully.")
