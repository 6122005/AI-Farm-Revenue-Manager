import pandas as pd
from app.services.ml_trainer import MLTrainer
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from pathlib import Path

df = DataPipeline.load_and_process_file(Path("data/Farm_Booking_Data_new.xlsx"))
MLTrainer.train_and_select_champion(df)
prediction_engine.reload_model()
print("Training complete!")
