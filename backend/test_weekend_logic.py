import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = DataPipeline.load_raw_dataframe(path)
print("Raw rows:", len(df))

# Reproduce the mapped_df creation roughly
mapped_df = df.copy()
date_col = "Start Date"
mapped_df["booking_date"] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
mapped_df["booking_date_dt"] = pd.to_datetime(mapped_df["booking_date"], errors="coerce")

print("Sat bookings:", len(mapped_df[mapped_df["booking_date_dt"].dt.dayofweek == 5]))
print("Sun bookings:", len(mapped_df[mapped_df["booking_date_dt"].dt.dayofweek == 6]))

# Wait, what if the dates are NaT?!
print("NaT dates:", mapped_df["booking_date_dt"].isna().sum())

# Let's print some dates
print("Sample dates:")
print(mapped_df["booking_date_dt"].head(10))
