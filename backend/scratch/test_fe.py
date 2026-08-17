from app.services.feature_engineering import FeatureEngineer
import pandas as pd
df = pd.DataFrame([{
    "booking_date": "2027-06-02",
    "start_datetime": "2027-06-05 19:00"
}])
res = FeatureEngineer.process_dataframe(df, is_prediction=True)
print(f"is_vacation in processed: {'is_vacation' in res.columns}")
if 'is_vacation' in res.columns:
    print(f"is_vacation value: {res['is_vacation'].iloc[0]}")
