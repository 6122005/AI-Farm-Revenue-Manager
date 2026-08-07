import pandas as pd

file_path = '/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx'
df = pd.read_excel(file_path, sheet_name='Events Export')

df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')

# Filter for August and September
df_aug_sep = df[df['Start Date'].dt.month.isin([8, 9])].copy()
df_aug_sep['Month'] = df_aug_sep['Start Date'].dt.month_name()

# Make sure Duration is a float and within 23 to 24 (since there's 23.5 etc)
df_aug_sep['Duration_num'] = pd.to_numeric(df_aug_sep['Duration'], errors='coerce')
df_24h = df_aug_sep[(df_aug_sep['Duration_num'] >= 23.0) & (df_aug_sep['Duration_num'] <= 24.0)].copy()

# Filter out festivals
# Keep if 'Festivals ' is 0, '0', or NaN
valid_festivals = [0, '0', 0.0]
df_24h['is_festival'] = ~df_24h['Festivals '].isin(valid_festivals) & df_24h['Festivals '].notna()

filtered_df = df_24h[
    (~df_24h['is_festival']) & 
    (df_24h['Rate'] > 1000)
]

print("--- Filtered 23/24 Hour Bookings Data ---")
print(filtered_df[['Start Date', 'Month', 'Duration', 'Weekend', 'Festivals ', 'Rate']].sort_values('Start Date').to_string())

print("\n--- Average Price (Excluding Festivals & 1000 Rs anomalies) ---")
avg_prices = filtered_df.groupby(['Month', 'Weekend'])['Rate'].mean().reset_index()
print(avg_prices)

