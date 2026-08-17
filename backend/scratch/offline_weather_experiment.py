import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.ml_trainer import MLTrainer

# Load Enriched Data
df_raw = DataPipeline.process_with_explicit_mapping(
    Path('data/Farm_Booking_Data_new_weather_enriched.xlsx'),
    price_col='Rate', date_col='Start Date', 
    slot_col='Booking Category', guests_col='Number of Guests', 
    lead_col='Lead Days', competitor_col='Competitor_Price'
)

# Pass through FeatureEngineer (this enriches base features, weather cols remain untouched if they exist)
features_df = FeatureEngineer.process_dataframe(df_raw.copy())

trainer = MLTrainer()

# --------------------------
# MODEL A (Current Baseline)
# --------------------------
features_a = features_df.copy()
# Explicitly drop weather features so it matches current production model
weather_cols = ['temperature_c', 'humidity_pct', 'rain_mm']
features_a.drop(columns=[c for c in weather_cols if c in features_a.columns], inplace=True)
report_a = trainer.train_and_select_champion(features_a)

# --------------------------
# MODEL B (+ Weather)
# --------------------------
features_b = features_df.copy()
report_b = trainer.train_and_select_champion(features_b)

def print_metrics(name, report):
    m = report['metrics']
    print(f"--- {name} ---")
    print(f"R²: {m['r2']*100:.2f}%")
    print(f"MAE: ₹{m['mae']:.0f}")
    print(f"RMSE: ₹{m['rmse']:.0f}")

print_metrics("Model A (No Weather)", report_a)
print_metrics("Model B (With Weather)", report_b)

# Feature Importance
print("\n--- Model B Feature Importance ---")
for f, imp in list(report_b.get('feature_importances', {}).items())[:15]:
    print(f"{f}: {imp:.4f}")

# Segment Analysis (Weather vs Price Correlation)
print("\n--- Weather vs Price Correlations ---")
print("Overall Temperature:", features_df['selling_price'].corr(features_df['temperature_c']))
print("Overall Humidity:", features_df['selling_price'].corr(features_df['humidity_pct']))
print("Overall Rain:", features_df['selling_price'].corr(features_df['rain_mm']))

# Save results for final report
with open('scratch/experiment_results.txt', 'w') as f:
    f.write(f"Model A R2: {report_a['metrics']['r2']}\n")
    f.write(f"Model B R2: {report_b['metrics']['r2']}\n")
    f.write(f"Model A MAE: {report_a['metrics']['mae']}\n")
    f.write(f"Model B MAE: {report_b['metrics']['mae']}\n")
