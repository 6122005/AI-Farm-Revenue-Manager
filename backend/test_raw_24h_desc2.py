import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

mask = df['Description'].astype(str).str.contains('24', case=False, na=False)
print("Sample descriptions with '24':")
print(df[mask]['Description'].head(20).tolist())

mask_24h = df['Description'].astype(str).str.contains('24 h', case=False, na=False) | df['Description'].astype(str).str.contains('24h', case=False, na=False)
print(f"Contains '24 h' or '24h': {len(df[mask_24h])}")

