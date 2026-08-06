import pandas as pd
df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Sheet4')
print(df[['festival_name', 'festival_date', 'window_start', 'window_end']])
