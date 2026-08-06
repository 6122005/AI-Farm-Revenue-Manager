import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

print(df[['Start Date', 'Start Time', 'End Date', 'End Time']].head(10))
