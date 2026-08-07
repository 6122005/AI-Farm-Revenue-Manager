import pandas as pd
import numpy as np

# Load data
df = pd.read_excel("data/Farm_Booking_Data_new.xlsx", sheet_name="Events Export")

# Clean column names
df.columns = df.columns.str.strip()

date_col = 'Start Date'
slot_col = 'Booking Category'
price_col = 'Rate'
guest_col = 'Number of Guests'

# Convert dates
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# Filter for January
df['Month'] = df[date_col].dt.month
jan_df = df[df['Month'] == 1].copy()

# Filter for 24H Night
target_slot = [s for s in jan_df[slot_col].unique() if pd.notna(s) and '24' in str(s) and 'Night' in str(s)]

if not target_slot:
    print("Could not find 24H Night slot in January data.")
else:
    jan_24_df = jan_df[jan_df[slot_col] == target_slot[0]].copy()
    
    # Clean price and guests
    jan_24_df['Guests'] = pd.to_numeric(jan_24_df[guest_col], errors='coerce')
    jan_24_df['Price'] = pd.to_numeric(jan_24_df[price_col].astype(str).str.replace(',', '').str.replace('₹', ''), errors='coerce')
    
    # Drop NaNs
    valid = jan_24_df.dropna(subset=['Guests', 'Price'])
    valid = valid.sort_values(by='Guests')
    
    print(f"--- JANUARY 24H NIGHT RECORDS ({len(valid)} records) ---")
    print(valid[[date_col, 'Guests', 'Price']].to_string(index=False))
    
    if len(valid) > 1:
        x = valid['Guests'].values
        y = valid['Price'].values
        
        if len(np.unique(x)) > 1:
            slope, intercept = np.polyfit(x, y, 1)
            print(f"\n--- CALCULATION ---")
            print(f"Calculated Per Person Increment (Slope): ₹{slope:.2f}")
        else:
            print("\nCannot calculate increment because all records have the exact same number of guests.")
