from app.services.prediction_engine import PredictionEngine
engine = PredictionEngine()
df = engine.df
subset = df[(df["month"] == 12) & (df["is_weekend"] == 0) & (df["slot_type"] == "24H Night")]
print("Subset for Dec Weekday 24H Night:")
print(subset[["booking_date", "month", "year", "selling_price", "base_selling_price", "cmv_base_price"]])
