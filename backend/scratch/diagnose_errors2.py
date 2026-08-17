import pandas as pd
from app.services.prediction_engine import prediction_engine
from app.services.ml_trainer import MLTrainer
import numpy as np

# 1. Get clean data
df = prediction_engine.get_clean_data()
if "selling_price" not in df.columns:
    print("selling_price not found")
    exit()

# Filter out missing prices
df = df[df["selling_price"] > 0].copy()

# 2. Train model and predict
trainer = MLTrainer()
trainer.train(df)

# Predictions
df["predicted_price"] = trainer.predict(df)
df["error"] = df["predicted_price"] - df["selling_price"]
df["abs_error"] = df["error"].abs()

print(f"Overall R²: {trainer.metrics.get('r2', 'N/A')}")
print(f"Overall MAE: {trainer.metrics.get('mae', 'N/A')}")

print("\n--- TOP 20 BIGGEST ERRORS ---")
top_errors = df.sort_values(by="abs_error", ascending=False).head(20)
cols_to_show = ["booking_date", "start_datetime", "commercial_slot", "person_count", "duration_hours", "selling_price", "predicted_price", "error", "abs_error"]
print(top_errors[cols_to_show].to_string())

# Group errors by slot
print("\n--- ERROR BY CATEGORY ---")
cat_errors = df.groupby("commercial_slot")["abs_error"].mean().sort_values(ascending=False)
print(cat_errors)

# Group errors by person_count
print("\n--- ERROR BY GUEST COUNT ---")
guest_errors = df.groupby(pd.cut(df["person_count"], bins=[0,4,10,20,100]))["abs_error"].mean()
print(guest_errors)

