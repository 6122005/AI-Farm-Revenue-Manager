import pandas as pd
df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')
df['Start Date'] = pd.to_datetime(df['Start Date'])
df['Month'] = df['Start Date'].dt.month
may_df = df[(df['Month'] == 5) & (df['Booking Category'] == '24H Night')]
print(may_df[['Start Date', 'Rate', 'Duration']])
