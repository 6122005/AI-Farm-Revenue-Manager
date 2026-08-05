import pandas as pd
from app.services.data_pipeline import CLEAN_DATA_PATH

df = pd.read_csv(CLEAN_DATA_PATH)
df = df[(df['selling_price'] >= 500) & (df['is_festival'] == 0)]
df = df[(df['is_weekend'] == 0) & (df['commercial_slot'] == '24H Day') & (df['month'] == 2)]
print("--- Raw Records ---")
print(df[['booking_date', 'person_count', 'selling_price']].to_string(index=False))
