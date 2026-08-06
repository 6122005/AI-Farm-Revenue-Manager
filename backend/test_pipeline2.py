import pandas as pd
df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')
print(df['Festivals '].dropna().unique())
