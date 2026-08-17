import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import pandas as pd
from datetime import datetime
from meteostat import Stations, Daily

# 1. Load Data
df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')

# 2. Extract unique dates
date_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["start date", "booking_date", "check_in", "event_date"])), None)
df['start_datetime'] = pd.to_datetime(df[date_col], errors='coerce')
unique_dates = df['start_datetime'].dt.date.dropna().unique()
print(f"Total Rows: {len(df)}")
print(f"Unique Stay Dates: {len(unique_dates)}")
print(f"Date Range: {min(unique_dates)} to {max(unique_dates)}")

# 3. Find Stations
LAT = 21.1702
LON = 72.8311
stations = Stations()
stations = stations.nearby(LAT, LON)
station_df = stations.fetch(10)

print("\nNearest Stations:")
print(station_df[['name', 'distance']])

# Evaluate the best station for our date range
start_dt = datetime.combine(min(unique_dates), datetime.min.time())
end_dt = datetime.combine(max(unique_dates), datetime.max.time())

best_station_id = None
best_data = None
best_missing_count = float('inf')

for station_id, row in station_df.iterrows():
    print(f"\nEvaluating Station: {row['name']} (ID: {station_id}) - Distance: {row['distance']:.1f} km")
    try:
        data = Daily(station_id, start=start_dt, end=end_dt)
        data_df = data.fetch()
        
        # Check coverage for the specific unique dates
        date_index = pd.DatetimeIndex([datetime.combine(d, datetime.min.time()) for d in unique_dates])
        
        # Find which dates are missing from the fetched data
        missing_dates = []
        temp_missing = 0
        rhum_missing = 0
        prcp_missing = 0
        
        for d in date_index:
            if d not in data_df.index:
                missing_dates.append(d)
                temp_missing += 1
                rhum_missing += 1
                prcp_missing += 1
            else:
                row_d = data_df.loc[d]
                if pd.isna(row_d['tavg']): temp_missing += 1
                if pd.isna(row_d.get('rhum')): rhum_missing += 1
                if pd.isna(row_d.get('prcp')): prcp_missing += 1
                
        total_missing_score = temp_missing + rhum_missing + prcp_missing
        print(f"  Missing Dates: {len(missing_dates)} / {len(unique_dates)}")
        print(f"  Missing Temp: {temp_missing}, RH: {rhum_missing}, Rain: {prcp_missing}")
        
        if total_missing_score < best_missing_count:
            best_missing_count = total_missing_score
            best_station_id = station_id
            best_data = data_df
            
            if total_missing_score == 0:
                print("  Perfect coverage found! Stopping search.")
                break
    except Exception as e:
        print(f"  Error fetching data: {e}")

print(f"\n--- BEST STATION SELECTED: {best_station_id} ---")
