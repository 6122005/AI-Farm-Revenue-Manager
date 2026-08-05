import pandas as pd
from app.services.data_pipeline import CLEAN_DATA_PATH

df = pd.read_csv(CLEAN_DATA_PATH)
festivals_df = df[df['is_festival'] == 1].copy()

if festivals_df.empty:
    print("No festival records found.")
else:
    # Select important columns
    cols = ['booking_date', 'commercial_slot', 'person_count', 'selling_price', 'season']
    festivals_df = festivals_df.sort_values(by='booking_date')
    
    print(f"Found {len(festivals_df)} festival records:\n")
    print(festivals_df[cols].to_string(index=False))
