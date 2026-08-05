import pandas as pd
from app.services.data_pipeline import CLEAN_DATA_PATH

df = pd.read_csv(CLEAN_DATA_PATH)
df = df[(df['selling_price'] >= 500) & (df['is_festival'] == 0)]
df = df[(df['is_weekend'] == 0) & (df['commercial_slot'] == '24H Night')]

months = [2, 7, 8, 9, 10, 11]
for m in months:
    sub = df[df['month'] == m]
    if not sub.empty:
        avg = sub['selling_price'].mean()
        guests = sub['person_count'].mean()
        print(f"Month {m}: Avg Price = {avg:.2f}, Avg Guests = {guests:.1f}, Count = {len(sub)}")
    else:
        print(f"Month {m}: No Data")
