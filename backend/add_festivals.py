import pandas as pd
file_path = 'data/Farm_Booking_Data_new.xlsx'
df_events = pd.read_excel(file_path, sheet_name='Sheet4')

new_events = [
    {'festival_name': 'Makar Sankranti', 'festival_date': pd.Timestamp('2027-01-14'), 'window_start': pd.Timestamp('2027-01-13 17:00:00'), 'window_end': pd.Timestamp('2027-01-15 17:00:00')},
    {'festival_name': 'Makar Sankranti', 'festival_date': pd.Timestamp('2028-01-14'), 'window_start': pd.Timestamp('2028-01-13 17:00:00'), 'window_end': pd.Timestamp('2028-01-15 17:00:00')},
    {'festival_name': 'Makar Sankranti', 'festival_date': pd.Timestamp('2029-01-14'), 'window_start': pd.Timestamp('2029-01-13 17:00:00'), 'window_end': pd.Timestamp('2029-01-15 17:00:00')},
    {'festival_name': 'Makar Sankranti', 'festival_date': pd.Timestamp('2030-01-14'), 'window_start': pd.Timestamp('2030-01-13 17:00:00'), 'window_end': pd.Timestamp('2030-01-15 17:00:00')}
]

df_new = pd.DataFrame(new_events)
df_events = pd.concat([df_events, df_new], ignore_index=True)

with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df_events.to_excel(writer, sheet_name='Sheet4', index=False)

print("Added Makar Sankranti 2027-2030 to Sheet4")
