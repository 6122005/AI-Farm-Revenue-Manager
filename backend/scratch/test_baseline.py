import pandas as pd
from app.services.prediction_engine import prediction_engine
df = prediction_engine.get_clean_data()
df = df.head(10).copy()
df["duration_hours"] = 7
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
res = HistoricalPricingBaseline.fit_predict_expanding(df)
print("Success!")
