import pandas as pd
import numpy as np
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
import json

df = DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))
df_feat = FeatureEngineer.process_dataframe(df)

drop_mask = pd.Series(False, index=df_feat.index)
if "commercial_slot" in df_feat.columns: drop_mask = drop_mask | (df_feat["commercial_slot"] == "Extended Day")
if "is_manual_outlier" in df_feat.columns: drop_mask = drop_mask | (df_feat["is_manual_outlier"] == 1)
df_clean = df_feat[~drop_mask].copy()

df_clean["guest_bucket"] = pd.cut(df_clean["person_count"], bins=[0, 4, 10, 20, 100], labels=["1-4", "5-10", "11-20", "20+"], right=True)
df_clean["dur_bucket"] = pd.cut(df_clean["duration_hours"], bins=[-1, 5.5, 8.5, 12.5, 18.5, 24.5, 100], labels=["1-5H", "6-8H", "9-12H", "13-18H", "19-24H", "24H+"])

segments = df_clean.groupby(["commercial_slot", "month", "is_weekend"])

results = []
guest_learnable = 0
dur_learnable = 0
noisy = 0
flat = 0
insufficient = 0

for (slot, month, weekend), group in segments:
    if len(group) < 3: 
        insufficient += 1
        continue
    
    # Guest Curve
    g_curve = group.groupby("guest_bucket")["selling_price"].median().dropna().to_dict()
    g_counts = group.groupby("guest_bucket")["selling_price"].count().to_dict()
    
    # Dur Curve
    d_curve = group.groupby("dur_bucket")["selling_price"].median().dropna().to_dict()
    
    # Classify Guest Relationship
    g_vals = list(g_curve.values())
    if len(g_vals) < 2:
        g_rel = "insufficient"
    else:
        diffs = np.diff(g_vals)
        if all(d > 50 for d in diffs): g_rel = "monotonic"
        elif all(abs(d) <= 50 for d in diffs): g_rel = "flat"
        else: g_rel = "noisy/contradictory"
        
    # Classify Dur Relationship
    d_vals = list(d_curve.values())
    if len(d_vals) < 2:
        d_rel = "insufficient"
    else:
        diffs = np.diff(d_vals)
        if all(d > 50 for d in diffs): d_rel = "monotonic"
        elif all(abs(d) <= 50 for d in diffs): d_rel = "flat"
        else: d_rel = "noisy/contradictory"
        
    if g_rel == "monotonic": guest_learnable += 1
    elif g_rel == "flat": flat += 1
    elif g_rel == "noisy/contradictory": noisy += 1
    
    if d_rel == "monotonic": dur_learnable += 1
    
    results.append({
        "slot": slot, "month": month, "weekend": weekend,
        "count": len(group),
        "P25": group["selling_price"].quantile(0.25),
        "P50": group["selling_price"].median(),
        "P75": group["selling_price"].quantile(0.75),
        "P90": group["selling_price"].quantile(0.90),
        "guest_rel": g_rel,
        "dur_rel": d_rel
    })

# Investigate High Price Underpredictions
high_price_targets = [
    ("24H Day", 3, 0),
    ("12H Day", 6, 1),
    ("12H Day", 2, 0),
    ("12H Day", 3, 0),
    ("24H Night", 6, 1)
]

hp_analysis = []
for slot, month, weekend in high_price_targets:
    sub = df_clean[(df_clean["commercial_slot"] == slot) & (df_clean["month"] == month) & (df_clean["is_weekend"] == weekend)]
    if sub.empty: continue
    
    p75 = sub["selling_price"].quantile(0.75)
    high_records = sub[sub["selling_price"] >= p75]
    normal_records = sub[sub["selling_price"] < p75]
    
    if high_records.empty or normal_records.empty: continue
    
    # Check features
    high_fest = high_records["is_festival"].mean()
    norm_fest = normal_records["is_festival"].mean()
    
    high_lead = high_records["lead_days"].mean()
    norm_lead = normal_records["lead_days"].mean()
    
    high_guests = high_records["person_count"].mean()
    norm_guests = normal_records["person_count"].mean()
    
    # Classification
    if high_fest > norm_fest or (high_guests - norm_guests > 5):
        classification = "PREDICTABLE HIGH-DEMAND"
        reason = f"Festivals: {high_fest:.1f} vs {norm_fest:.1f} | Guests: {high_guests:.1f} vs {norm_guests:.1f}"
    else:
        classification = "UNEXPLAINED HISTORICAL PRICE"
        reason = f"No major driver diff. Guests: {high_guests:.1f} vs {norm_guests:.1f} | Lead: {high_lead:.1f} vs {norm_lead:.1f}"
        
    hp_analysis.append({
        "segment": f"{slot} M{month} W{weekend}",
        "high_avg": high_records["selling_price"].mean(),
        "norm_avg": normal_records["selling_price"].mean(),
        "classification": classification,
        "reason": reason
    })

summary = {
    "total_segments_analyzed": len(results),
    "guest_learnable": guest_learnable,
    "dur_learnable": dur_learnable,
    "flat": flat,
    "noisy": noisy,
    "insufficient": insufficient,
    "high_price_investigation": hp_analysis
}

print(json.dumps(summary, indent=2))
pd.DataFrame(results).to_csv("scratch/deep_elasticity_audit.csv", index=False)
