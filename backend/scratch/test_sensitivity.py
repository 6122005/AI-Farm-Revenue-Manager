import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from app.config import MODELS_DIR

# Load the champion model artifact
artifact_path = MODELS_DIR / "champion_model.joblib"
artifact = joblib.load(artifact_path)
model = artifact["model"]["base_model"]
features = artifact["features"]

# Create a baseline row
base_row = {f: 0 for f in features}

# Let's set some default values for a standard booking
base_row["person_count"] = 10
base_row["lead_days"] = 7
base_row["duration_hours"] = 24
base_row["is_weekend"] = 1
base_row["month"] = 5  # Summer
base_row["commercial_slot_24H NIGHT"] = 1 # Assuming OHE
base_row["slot_type_24H Night"] = 1

# If the exact columns don't match due to preprocessing, we just find matching
for f in features:
    if "24H NIGHT" in str(f).upper():
        base_row[f] = 1
    if "WEEKEND" in str(f).upper() and "RATIO" not in str(f).upper() and "AVG" not in str(f).upper():
        base_row[f] = 1

# Let's assume a historical baseline price of ₹7000 for this
base_price = 7000.0

print("========================================")
print("PERSON COUNT SENSITIVITY TEST")
print("========================================")
print(f"Base Configuration: 24H Night, Weekend, Lead Days: 7, Base Price: ₹{base_price}")
print(f"{'Guests':<10} | {'Residual':<10} | {'Total Price':<10} | {'Diff from Prev'}")
print("-" * 55)

prev_price = None
for guests in [2, 5, 10, 15, 18, 20, 25]:
    row = base_row.copy()
    row["person_count"] = guests
    
    # Predict residual
    X = pd.DataFrame([row])[features]
    residual = model.predict(X)[0]
    total_price = base_price + residual
    
    diff_str = ""
    if prev_price is not None:
        diff = total_price - prev_price
        diff_str = f"+₹{diff:.2f}" if diff >= 0 else f"-₹{abs(diff):.2f}"
    
    print(f"{guests:<10} | ₹{residual:<9.2f} | ₹{total_price:<9.2f} | {diff_str}")
    prev_price = total_price


print("\n========================================")
print("LEAD DAYS SENSITIVITY TEST")
print("========================================")
print(f"Base Configuration: 24H Night, Weekend, Guests: 15, Base Price: ₹{base_price}")
print(f"{'Lead Days':<10} | {'Residual':<10} | {'Total Price':<10} | {'Diff from 0'}")
print("-" * 55)

base_row["person_count"] = 15
price_at_0 = None

for ld in [0, 1, 3, 7, 14, 30, 60]:
    row = base_row.copy()
    row["lead_days"] = ld
    
    X = pd.DataFrame([row])[features]
    residual = model.predict(X)[0]
    total_price = base_price + residual
    
    if price_at_0 is None:
        price_at_0 = total_price
        
    diff = total_price - price_at_0
    diff_str = f"+₹{diff:.2f}" if diff >= 0 else f"-₹{abs(diff):.2f}"
    
    print(f"{ld:<10} | ₹{residual:<9.2f} | ₹{total_price:<9.2f} | {diff_str}")

