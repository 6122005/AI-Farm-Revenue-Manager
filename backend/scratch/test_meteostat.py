import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import pandas as pd
from datetime import datetime
import meteostat
from meteostat import Daily

LAT = 21.1702
LON = 72.8311

stations = meteostat.stations.nearby(LAT, LON)
station_df = stations.fetch(10)
print(station_df[['name', 'distance']])
