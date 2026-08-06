import pandas as pd
file_path = 'data/Farm_Booking_Data_new.xlsx'
df = pd.read_excel(file_path, sheet_name='Events Export')
print("Events Export Columns:", df.columns.tolist())
