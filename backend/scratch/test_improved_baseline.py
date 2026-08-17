import sys
from pathlib import Path
import pandas as pd
import numpy as np

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.data_pipeline import DataPipeline

excel_path = backend_dir / "data" / "Farm_Booking_Data_new.xlsx"
df_pipeline = DataPipeline.load_and_process_file(excel_path)

cond_not_extended = (df_pipeline['commercial_slot'] != 'Extended Day') & (df_pipeline['is_extended_booking'] == 0) & (df_pipeline['extended_stay'] == False)
cond_not_festival = (df_pipeline['is_festival'] == 0)
outlier_col_str = df_pipeline['outlier'].fillna('').astype(str).str.lower()
cond_not_outlier = (outlier_col_str != 'outlier') & (df_pipeline['is_manual_outlier'] == 0) & (df_pipeline['is_global_outlier'] == False)

df_clean = df_pipeline[cond_not_extended & cond_not_festival & cond_not_outlier].copy().reset_index(drop=True)

# 1. Base price computed for 4-guest baseline:
# Strip guest count effect from selling_price assuming ₹200 per guest over 4:
df_clean['base_4guest_price'] = df_clean['selling_price'] - np.maximum(0, df_clean['person_count'] - 4) * 200.0

# 2. Segment Medians on 4-guest base price:
segment_medians = df_clean.groupby(['month', 'commercial_slot', 'is_weekend'])['base_4guest_price'].median().reset_index()
segment_medians.rename(columns={'base_4guest_price': 'segment_median_base'}, inplace=True)

df_eval = pd.merge(df_clean, segment_medians, on=['month', 'commercial_slot', 'is_weekend'], how='left')

# Fallbacks:
m_slot_med = df_clean.groupby(['month', 'commercial_slot'])['base_4guest_price'].median().to_dict()
slot_w_med = df_clean.groupby(['commercial_slot', 'is_weekend'])['base_4guest_price'].median().to_dict()
slot_med = df_clean.groupby('commercial_slot')['base_4guest_price'].median().to_dict()

preds = []
for idx, row in df_eval.iterrows():
    m = row['month']
    slot = row['commercial_slot']
    w = row['is_weekend']
    guests = row['person_count']
    
    base = row['segment_median_base']
    if pd.isna(base):
        base = m_slot_med.get((m, slot), slot_w_med.get((slot, w), slot_med.get(slot, 2500.0)))
        
    # Re-add guest increment for guests > 4
    extra_guests = max(0, guests - 4)
    guest_adj = extra_guests * 250.0
    
    pred = round(base + guest_adj, -1)
    preds.append(pred)

df_eval['pred_price'] = preds
df_eval['abs_err'] = (df_eval['pred_price'] - df_eval['selling_price']).abs()
df_eval['err_pct'] = df_eval['abs_err'] / df_eval['selling_price'] * 100.0

mae = df_eval['abs_err'].mean()
median_ae = df_eval['abs_err'].median()
within_200 = (df_eval['abs_err'] <= 200).mean() * 100
within_300 = (df_eval['abs_err'] <= 300).mean() * 100
within_500 = (df_eval['abs_err'] <= 500).mean() * 100

print(f"--- IMPROVED BASELINE + GUEST ADJ TEST ---")
print(f"MAE: ₹{mae:.2f}")
print(f"Median Absolute Error: ₹{median_ae:.2f}")
print(f"Within ₹200 Error: {within_200:.2f}%")
print(f"Within ₹300 Error: {within_300:.2f}%")
print(f"Within ₹500 Error: {within_500:.2f}%")
