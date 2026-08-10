from app.services.prediction_engine import PredictionEngine
import warnings
warnings.filterwarnings("ignore")
engine = PredictionEngine()
engine.predict({"start_datetime": "2026-11-04 19:00", "end_datetime": "2026-11-05 19:00", "commercial_slot": "24H Night", "person_count": 10})
df = engine._clean_data_cache
row = df[df['booking_date'] == "2024-11-03"].iloc[0]
print("booking_date:", row['booking_date'])
print("day_of_week:", row['day_of_week'])
print("is_weekend:", row['is_weekend'])
