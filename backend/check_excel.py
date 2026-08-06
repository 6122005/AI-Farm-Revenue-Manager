import pandas as pd
df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')
print("Total rows:", len(df))
print("\nSample columns:")
print(df.columns.tolist())
print("\nSample of Rate column:")
print(df['Rate'].describe())
print("\nSample 24H Night rows:")
night24 = df[df['Booking Category'].astype(str).str.contains('24H Night')]
print(night24[['Booking Category', 'Rate', 'person_count']].head(10))
