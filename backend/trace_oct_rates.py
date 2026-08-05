from app.services.guest_pricing_engine import guest_pricing_engine
import pandas as pd
from app.services.data_pipeline import CLEAN_DATA_PATH

df = pd.read_csv(CLEAN_DATA_PATH)
df = df[(df['selling_price'] >= 500) & (df['is_festival'] == 0)]

norm_slot = "24H Night"
df['norm_slot'] = "24H Night" # simplified

mask = (df['month'] == 10) & (df['commercial_slot'] == "24H Night")
sub_df = df[mask].copy()

grouped = sub_df.groupby('person_count')['selling_price'].median().reset_index()
grouped = grouped.sort_values(by='person_count')
print(grouped)
