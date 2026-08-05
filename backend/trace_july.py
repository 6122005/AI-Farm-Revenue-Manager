import pandas as pd
from app.services.data_pipeline import CLEAN_DATA_PATH

df = pd.read_csv(CLEAN_DATA_PATH)
df = df[(df['selling_price'] >= 500) & (df['is_festival'] == 0)]
df = df[(df['is_weekend'] == 1) & (df['commercial_slot'] == '24H Night') & (df['month'] == 7)]
print(df[['person_count', 'selling_price', 'is_weekend']])
