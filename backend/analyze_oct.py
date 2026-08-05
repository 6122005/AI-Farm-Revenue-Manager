import pandas as pd

df = pd.read_excel("data/Farm_Booking_Data_new.xlsx", sheet_name="Events Export")
df["Start Date Str"] = df["Start Date"].astype(str)

oct_df = df[(df["Start Date Str"].str.contains("-10-")) & (df["Booking Category"] == "24H Night") & (df["Weekend"] == 1)]
print("October 24H Night Weekend:")
print(oct_df[["Start Date", "Number of Guests", "Rate", "Festivals ", "Lead Days"]])

feb_df = df[(df["Start Date Str"].str.contains("-02-")) & (df["Booking Category"] == "24H Night") & (df["Weekend"] == 1)]
print("\nFebruary 24H Night Weekend:")
print(feb_df[["Start Date", "Number of Guests", "Rate", "Festivals ", "Lead Days"]])
