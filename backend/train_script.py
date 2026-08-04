import pandas as pd
from app.api.upload import MLTrainer
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from pathlib import Path

df = DataPipeline.process_with_explicit_mapping(
    file_path=Path("data/Farm_Booking_Data.xlsx"),
    price_col="selling_price",
    date_col="booking_date",
    slot_col="commercial_slot",
    guests_col="person_count",
    lead_col="lead_days",
    competitor_col="competitor_price"
)
MLTrainer.train_and_select_champion(df)
prediction_engine.reload_model()
print("Training complete!")
