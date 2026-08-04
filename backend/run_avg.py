import pandas as pd
from app.services.feature_engineering import FeatureEngineer
from app.services.data_pipeline import DataPipeline

df = pd.read_csv("data/clean_booking_data.csv")
enriched = FeatureEngineer.process_dataframe(df)
FeatureEngineer.calculate_group_averages(enriched)
print("Averages recalculated!")
