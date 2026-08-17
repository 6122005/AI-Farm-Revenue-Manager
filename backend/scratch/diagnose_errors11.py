import pandas as pd
from pathlib import Path

df = pd.read_excel(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"), sheet_name="Events Export")
df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce")
df["Number of Guests"] = pd.to_numeric(df["Number of Guests"], errors="coerce")

df_24n = df[df["Booking Category"].astype(str).str.upper() == "24H NIGHT"].dropna(subset=["Rate", "Number of Guests"])
print("\n--- 24H Night Rates vs Guests ---")
for g, r in zip(df_24n["Number of Guests"].head(20), df_24n["Rate"].head(20)):
    print(f"Guests: {g} -> Rate: {r}")

print("\n--- Correlation ---")
print(df_24n[["Number of Guests", "Rate"]].corr())

