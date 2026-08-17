import sys
from pathlib import Path
import pandas as pd
import numpy as np

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.data_pipeline import DataPipeline

excel_path = backend_dir / "data" / "Farm_Booking_Data_new.xlsx"
df_pipeline = DataPipeline.load_and_process_file(excel_path)

# Strictly clean records: no extended day, no festival, no outlier
cond_not_extended = (df_pipeline['commercial_slot'] != 'Extended Day') & (df_pipeline['is_extended_booking'] == 0) & (df_pipeline['extended_stay'] == False)
cond_not_festival = (df_pipeline['is_festival'] == 0)
outlier_col_str = df_pipeline['outlier'].fillna('').astype(str).str.lower()
cond_not_outlier = (outlier_col_str != 'outlier') & (df_pipeline['is_manual_outlier'] == 0) & (df_pipeline['is_global_outlier'] == False)

df_clean = df_pipeline[cond_not_extended & cond_not_festival & cond_not_outlier].copy().reset_index(drop=True)
print(f"Total Clean Records for Benchmark: {len(df_clean)}")

# 1. Compute exact segment medians (Month, Commercial Slot, Weekend)
segment_medians = df_clean.groupby(['month', 'commercial_slot', 'is_weekend'])['selling_price'].median().reset_index()
segment_medians.rename(columns={'selling_price': 'segment_median_price'}, inplace=True)
print(f"Segment Medians count: {len(segment_medians)}")

# Merge segment medians back
df_eval = pd.merge(df_clean, segment_medians, on=['month', 'commercial_slot', 'is_weekend'], how='left')

# Fallback 1: Month x Commercial Slot
month_slot_medians = df_clean.groupby(['month', 'commercial_slot'])['selling_price'].median().to_dict()
# Fallback 2: Commercial Slot x Weekend
slot_weekend_medians = df_clean.groupby(['commercial_slot', 'is_weekend'])['selling_price'].median().to_dict()
# Fallback 3: Commercial Slot
slot_medians = df_clean.groupby('commercial_slot')['selling_price'].median().to_dict()

preds = []
for idx, row in df_eval.iterrows():
    m = row['month']
    slot = row['commercial_slot']
    w = row['is_weekend']
    actual = row['selling_price']
    guests = row['person_count']
    
    # 1. Base price lookup
    base = row['segment_median_price']
    if pd.isna(base):
        base = month_slot_medians.get((m, slot), slot_weekend_medians.get((slot, w), slot_medians.get(slot, 2500.0)))
        
    # 2. Guest adjustment: Base capacity = 4. If guests > 4, add guest fee
    # But wait, in historical dataset, does segment_median already reflect average guests?
    # Let's check guest increment adjustment
    guest_diff = max(0, guests - 4)
    # If base price was trained/learned on 4-guest baseline:
    # Let's test pure segment median vs adjusted
    
    pred = round(base, -1)
    preds.append(pred)

df_eval['pred_price'] = preds
df_eval['abs_err'] = (df_eval['pred_price'] - df_eval['selling_price']).abs()
df_eval['err_pct'] = df_eval['abs_err'] / df_eval['selling_price'] * 100.0

mae = df_eval['abs_err'].mean()
median_ae = df_eval['abs_err'].median()
within_200 = (df_eval['abs_err'] <= 200).mean() * 100
within_500 = (df_eval['abs_err'] <= 500).mean() * 100
within_5pct = (df_eval['err_pct'] <= 5.0).mean() * 100

print(f"\n--- BENCHMARK TEST: Segment Median Baseline Engine ---")
print(f"MAE: ₹{mae:.2f}")
print(f"Median Absolute Error: ₹{median_ae:.2f}")
print(f"Within ₹200 Error: {within_200:.2f}%")
print(f"Within ₹500 Error: {within_500:.2f}%")
print(f"Within 5% Margin: {within_5pct:.2f}%")
