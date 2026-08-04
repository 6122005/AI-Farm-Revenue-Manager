from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.ml_trainer import MLTrainer
import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
print("Loading and processing data...")
df = DataPipeline.load_and_process_file(file_path)
DataPipeline.sync_to_db(df)
df.to_csv("data/clean_booking_data.csv", index=False)

print("Applying feature engineering & regenerating group averages...")
enriched_df = FeatureEngineer.process_dataframe(df, is_prediction=False)

print("Retraining model...")
champion_artifact = MLTrainer.train_and_select_champion(enriched_df)
print(champion_artifact)

print("Regenerating Matrix...")
import generate_matrix
