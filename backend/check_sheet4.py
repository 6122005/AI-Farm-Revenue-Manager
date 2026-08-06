import pandas as pd
file_path = 'data/Farm_Booking_Data_new.xlsx'
try:
    df = pd.read_excel(file_path, sheet_name='Sheet4')
    print("Sheet4 Columns:", df.columns.tolist())
    print(df.head())
except Exception as e:
    print(e)
