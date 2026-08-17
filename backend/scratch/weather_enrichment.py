import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime, date
import meteostat

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

LAT = 21.1702
LON = 72.8311

# 1. Find Stations
st = meteostat.stations.nearby(meteostat.Point(LAT, LON))
station_df = st.head(5)
print("=== BEST METEOSTAT STATIONS NEAR FARMHOUSE ===")
print(station_df[['name', 'distance']])
best_station_id = station_df.index[0]
best_station_name = station_df.iloc[0]['name']
best_station_dist = station_df.iloc[0]['distance']
print(f"\nSelected Station: {best_station_name} (ID: {best_station_id}) - Distance: {best_station_dist:.1f} km")

# 2. Extract unique dates from dataset
df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')
date_col = 'Start Date'
df['start_datetime'] = pd.to_datetime(df[date_col], errors='coerce')
unique_dates = df['start_datetime'].dt.date.dropna().unique()
unique_dates = [d for d in unique_dates if d.year > 2020]

print(f"\nTotal Bookings: {len(df)}")
print(f"Unique Stay Dates: {len(unique_dates)}")

# 3. Fetch Weather Data for the Date Range
start_dt = datetime.combine(min(unique_dates), datetime.min.time())
end_dt = datetime.combine(max(unique_dates), datetime.max.time())

print(f"Fetching historical data from {start_dt.date()} to {end_dt.date()}...")
try:
    ts = meteostat.daily(best_station_id, start_dt, end_dt)
    weather_data = ts.fetch()
except Exception as e:
    print(f"Failed to fetch from station: {e}")
    print("Falling back to Point interpolation...")
    pt = meteostat.Point(LAT, LON)
    ts = meteostat.daily(pt, start_dt, end_dt)
    weather_data = ts.fetch()
    best_station_name = "Point Interpolation"

# 4. Audit coverage
missing_dates = []
temp_missing = 0
rhum_missing = 0
prcp_missing = 0

date_index = pd.DatetimeIndex([datetime.combine(d, datetime.min.time()) for d in unique_dates])

# Map to the dataset
weather_map = {}
for d in date_index:
    if d not in weather_data.index:
        missing_dates.append(d.date())
        temp_missing += 1
        rhum_missing += 1
        prcp_missing += 1
        weather_map[d.date()] = {'temperature_c': None, 'humidity_pct': None, 'rain_mm': None}
    else:
        row = weather_data.loc[d]
        t = row['tavg']
        h = row.get('rhum')
        r = row.get('prcp')
        if pd.isna(t): temp_missing += 1
        if pd.isna(h): rhum_missing += 1
        if pd.isna(r): prcp_missing += 1
        weather_map[d.date()] = {
            'temperature_c': float(t) if pd.notna(t) else None,
            'humidity_pct': float(h) if pd.notna(h) else None,
            'rain_mm': float(r) if pd.notna(r) else None
        }

print("\n=== DATA COMPLETENESS AUDIT ===")
print(f"Total Unique Dates: {len(unique_dates)}")
print(f"Dates Retrieved: {len(unique_dates) - len(missing_dates)}")
print(f"Missing Entire Date: {len(missing_dates)}")
print(f"Missing Temperature: {temp_missing}")
print(f"Missing Humidity: {rhum_missing}")
print(f"Missing Rain: {prcp_missing}")

# 5. Enrich Dataset
df['booking_date_only'] = df['start_datetime'].dt.date
df['temperature_c'] = df['booking_date_only'].apply(lambda d: weather_map.get(d, {}).get('temperature_c'))
df['humidity_pct'] = df['booking_date_only'].apply(lambda d: weather_map.get(d, {}).get('humidity_pct'))
df['rain_mm'] = df['booking_date_only'].apply(lambda d: weather_map.get(d, {}).get('rain_mm'))

df.drop(columns=['start_datetime', 'booking_date_only'], inplace=True)
output_path = 'data/Farm_Booking_Data_new_weather_enriched.xlsx'
df.to_excel(output_path, index=False)
print(f"\nSaved enriched dataset to {output_path}")

