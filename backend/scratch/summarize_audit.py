import pandas as pd

df = pd.read_csv("scratch/elasticity_audit.csv")

# 1. Monotonicity Flatlining
flat_guest = df["guest_flatlined"].sum()
flat_dur = df["dur_flatlined"].sum()
total_segments = len(df)
print(f"Guest Flatlined Segments: {flat_guest}/{total_segments}")
print(f"Duration Flatlined Segments: {flat_dur}/{total_segments}")

# 2. High Price Underprediction
print("\nTop 5 Underpredicted Segments (High Price Bias):")
underpredicted = df.sort_values(by="high_price_bias", ascending=True).head(5)
for _, r in underpredicted.iterrows():
    print(f"{r['slot']} - Month {r['month']} - Wknd {r['weekend']}: Bias {r['high_price_bias']:.0f} (P90: {r['p90_price']:.0f})")
    
# 3. Couple HD vs 12H Day
print("\nCouple HD vs 12H Day Bias:")
couple_hd = df[df["slot"] == "Couple Half Day"]["bias"].mean()
day_12h = df[df["slot"] == "12H Day"]["bias"].mean()
print(f"Couple HD mean bias: {couple_hd:.2f}")
print(f"12H Day mean bias: {day_12h:.2f}")

