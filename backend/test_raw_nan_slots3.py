import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

end_d_col = next((c for c in df.columns if "end date" in str(c).lower() or "checkout_date" in str(c).lower()), None)
date_col = "Start Date"
print(f"end_d_col = {end_d_col}")

for idx, row in df.head(5).iterrows():
    sd_val = row.get(date_col)
    ed_val = row.get(end_d_col)
    
    sd = pd.to_datetime(sd_val)
    ed = pd.to_datetime(ed_val)
    
    diff = (ed - sd).total_seconds() / 3600.0
    print(f"Row {idx}: {sd} -> {ed} | diff = {diff}")

