import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, date
import httpx

# 1. SETUP
LAT = 21.1702
LON = 72.8311
TIMEZONE = "Asia/Kolkata"

df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')

# 2. EXTRACT DATES
date_col = 'Start Date'
df['start_datetime'] = pd.to_datetime(df[date_col], errors='coerce')
unique_dates_full = df['start_datetime'].dt.date.dropna().unique()
# Keep valid dates only
unique_dates = sorted([d for d in unique_dates_full if d.year > 2020])

start_dt_str = unique_dates[0].strftime("%Y-%m-%d")
# Open-meteo archive requires end_date to be up to 5 days ago, so let's bound it safely to today
end_dt_str = min(unique_dates[-1], datetime.now().date()).strftime("%Y-%m-%d")

# 3. CALL OPEN-METEO ARCHIVE
url = (
    f"https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LAT}&longitude={LON}"
    f"&start_date={start_dt_str}&end_date={end_dt_str}"
    f"&daily=temperature_2m_mean,relative_humidity_2m_mean,precipitation_sum,rain_sum"
    f"&timezone={TIMEZONE}"
)

print(f"Fetching Open-Meteo ERA5 Reanalysis data: {start_dt_str} to {end_dt_str}")
r = httpx.get(url, timeout=30.0)
if r.status_code != 200:
    print(f"Error fetching data: {r.status_code} {r.text}")
    sys.exit(1)

data = r.json()
daily = data.get("daily", {})
times = daily.get("time", [])
temps = daily.get("temperature_2m_mean", [])
hums = daily.get("relative_humidity_2m_mean", [])
rains = daily.get("precipitation_sum", [])

weather_map = {}
for i, t_str in enumerate(times):
    d = datetime.strptime(t_str, "%Y-%m-%d").date()
    weather_map[d] = {
        'temperature_c': temps[i],
        'humidity_pct': hums[i],
        'rain_mm': rains[i]
    }

# 4. AUDIT
missing_dates = []
temp_missing = 0
rhum_missing = 0
prcp_missing = 0

for d in unique_dates:
    if d not in weather_map:
        missing_dates.append(d)
        temp_missing += 1
        rhum_missing += 1
        prcp_missing += 1
    else:
        w = weather_map[d]
        if w['temperature_c'] is None: temp_missing += 1
        if w['humidity_pct'] is None: rhum_missing += 1
        if w['rain_mm'] is None: prcp_missing += 1

print("\n=== DATA COMPLETENESS AUDIT ===")
print(f"Total Unique Dates: {len(unique_dates)}")
print(f"Missing Entire Date: {len(missing_dates)}")
print(f"Missing Temperature: {temp_missing}")
print(f"Missing Humidity: {rhum_missing}")
print(f"Missing Rain: {prcp_missing}")

# 5. ENRICH DATAFRAME
df['booking_date_only'] = df['start_datetime'].dt.date

def get_w(d, key):
    if d in weather_map and weather_map[d][key] is not None:
        return weather_map[d][key]
    return np.nan

df['temperature_c'] = df['booking_date_only'].apply(lambda d: get_w(d, 'temperature_c'))
df['humidity_pct'] = df['booking_date_only'].apply(lambda d: get_w(d, 'humidity_pct'))
df['rain_mm'] = df['booking_date_only'].apply(lambda d: get_w(d, 'rain_mm'))

df.drop(columns=['start_datetime', 'booking_date_only'], inplace=True)
out_path = 'data/Farm_Booking_Data_new_weather_enriched.xlsx'
df.to_excel(out_path, index=False)
print(f"\nSaved enriched dataset to {out_path}")
