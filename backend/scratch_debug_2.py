import pandas as pd
df = pd.read_excel("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx", sheet_name="Events Export")
print(df["Booking Category"].value_counts(dropna=False))
