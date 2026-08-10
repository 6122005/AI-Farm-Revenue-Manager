import pandas as pd
from pathlib import Path

try:
    df = pd.read_csv("data/clean_booking_data.csv")
    print("Counts in clean_booking_data.csv:")
    print(df["booking_category"].value_counts())
    
    df_new = pd.read_excel("data/Farm_Booking_Data_new.xlsx", sheet_name="Events Export")
    print("\nCounts in Farm_Booking_Data_new.xlsx:")
    print(df_new["Booking Category"].value_counts())
    
except Exception as e:
    print(e)
