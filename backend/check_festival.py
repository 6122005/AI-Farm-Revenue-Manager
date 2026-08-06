import pandas as pd
from app.services.data_pipeline import CLEAN_DATA_PATH
df = pd.read_csv(CLEAN_DATA_PATH)
df['booking_date'] = pd.to_datetime(df['booking_date'])
may_df = df[(df['booking_date'].dt.month == 5) & (df['commercial_slot'] == '24H Night')]
print(may_df[['booking_date', 'selling_price', 'is_festival']])
