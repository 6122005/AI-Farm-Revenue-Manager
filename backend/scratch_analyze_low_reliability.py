import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.services.prediction_engine import prediction_engine
from datetime import datetime

slots = ["12H Day", "12H Night", "24 Hour Day", "24 Hour Night"] # Oh wait, "24H Night" in Excel, but in backend it might be "24 Hour Day" etc.
months = list(range(1, 13))

async def find_all_confidences():
    scenarios = []
    
    for month in months:
        for slot in slots:
            for is_weekend in [0, 1]:
                target_dt = None
                for day in range(1, 15):
                    hour = 19 if "Night" in slot else 10
                    test_dt = datetime(2026, month, day, hour, 0)
                    dow = test_dt.weekday()
                    calc_weekend = 0
                    if dow == 5 and "Night" in slot and test_dt.hour >= 17:
                        calc_weekend = 1
                    elif dow == 6 and "Day" in slot and 6 <= test_dt.hour <= 12:
                        calc_weekend = 1
                    if calc_weekend == is_weekend:
                        target_dt = test_dt
                        break
                        
                if not target_dt:
                    continue
                
                req = {
                    "start_datetime": target_dt.strftime("%Y-%m-%d %H:%M"),
                    "end_datetime": target_dt.strftime("%Y-%m-%d %H:%M"),
                    "commercial_slot": slot,
                    "person_count": 10
                }
                
                try:
                    res_dict = prediction_engine.predict(req)
                    scenarios.append({
                        "Month": month,
                        "Slot": slot,
                        "Day Type": "Weekend" if is_weekend else "Weekday",
                        "Level": res_dict["debug_audit"].get("level_used", "N/A"),
                        "Confidence": res_dict["debug_audit"].get("confidence", 0),
                        "Reliability": res_dict["reliability_level"]
                    })
                except Exception as e:
                    pass

    import pandas as pd
    df = pd.DataFrame(scenarios)
    if not df.empty:
        print(df["Reliability"].value_counts())
        low_df = df[df["Reliability"] == "Low"]
        if not low_df.empty:
            print("--- LOW RELIABILITY SCENARIOS ---")
            print(low_df.to_string(index=False))
            low_df.to_csv("low_reliability_report.csv", index=False)
        else:
            print("No Low Reliability scenarios.")
    else:
        print("Dataframe is completely empty!")

if __name__ == "__main__":
    asyncio.run(find_all_confidences())
