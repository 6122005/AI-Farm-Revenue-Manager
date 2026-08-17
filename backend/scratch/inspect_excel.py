import pandas as pd
from pathlib import Path
df = pd.read_excel(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"), sheet_name="Events Export")
cols = ["Start Date", "Title", "Rate", "Number of Guests", "Lead Days"]
print("\n--- JUNE 6 2026 ---")
print(df[df["Start Date"].astype(str).str.contains("2026-06-06", na=False)][cols])
print("\n--- JUNE 27 2026 ---")
print(df[df["Start Date"].astype(str).str.contains("2026-06-27", na=False)][cols])
print("\n--- MARCH 02 2026 ---")
print(df[df["Start Date"].astype(str).str.contains("2026-03-02", na=False)][cols])
print("\n--- MAY 05 2026 ---")
print(df[df["Start Date"].astype(str).str.contains("2026-05-05", na=False)][cols])
