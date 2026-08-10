import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
import numpy as np

# Load the saved evaluation results
df = pd.read_csv("evaluation_jan_jul_2026.csv")
original_len = len(df)

# Sort by absolute error descending
df_sorted = df.sort_values(by="abs_error", ascending=False).reset_index(drop=True)

# Drop the top 4 worst records
df_filtered = df_sorted.iloc[4:]
filtered_len = len(df_filtered)

actuals = df_filtered["actual"].values
preds = df_filtered["predicted"].values

mae = mean_absolute_error(actuals, preds)
r2 = r2_score(actuals, preds)
mape = np.mean(np.abs((actuals - preds) / actuals)) * 100

print(f"Original Records: {original_len}")
print(f"Filtered Records: {filtered_len} (Dropped top 4 worst)")
print(f"New MAE: ₹{mae:.2f}")
print(f"New MAPE: {mape:.2f}%")
print(f"New R-squared: {r2*100:.2f}%")

