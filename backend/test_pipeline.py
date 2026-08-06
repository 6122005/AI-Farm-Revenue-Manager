import pandas as pd
from app.services.demand_event_engine import demand_event_engine

df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')
fest_col = next((c for c in df.columns if "festival" in str(c).lower()), None)
print("Fest col found:", fest_col)

def map_event_id(x):
    if pd.isna(x) or str(x).strip() == "" or str(x).strip() == "0":
        return None
    return demand_event_engine.get_canonical_id(str(x))

if fest_col:
    events = df[fest_col].apply(map_event_id)
    print("Non-null canonical IDs:", events.dropna().tolist()[:10])
