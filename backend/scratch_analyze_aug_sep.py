import pandas as pd

file_path = '/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx'
df = pd.read_excel(file_path, sheet_name='Events Export')

# Convert Start Date to datetime
df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
# Filter for August and September
df_aug_sep = df[df['Start Date'].dt.month.isin([8, 9])].copy()
df_aug_sep['Month'] = df_aug_sep['Start Date'].dt.month_name()

# Convert Rate to numeric
df_aug_sep['Rate'] = pd.to_numeric(df_aug_sep['Rate'], errors='coerce')

# Check the distribution
# Weekend column might be True/False, 1/0, or string. Let's see.
print("--- Average Rate by Month, Weekend, and Duration ---")
avg_rate = df_aug_sep.groupby(['Month', 'Duration', 'Weekend'])['Rate'].mean().reset_index()
print(avg_rate)

print("\n--- Count by Month, Weekend, and Duration ---")
count = df_aug_sep.groupby(['Month', 'Duration', 'Weekend'])['Rate'].count().reset_index()
print(count)

print("\n--- Detailed August & September 24 Hours bookings ---")
df_24h = df_aug_sep[df_aug_sep['Duration'].astype(str).str.contains('24', case=False, na=False)]
print(df_24h[['Start Date', 'Day of Week ', 'Weekend', 'Festivals ', 'Rate']].sort_values('Start Date').to_string())

