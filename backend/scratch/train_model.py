import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.ml_trainer import MLTrainer

file_path = Path("data/Farm_Booking_Data_new.xlsx")

df_raw = DataPipeline.process_with_explicit_mapping(
    file_path, price_col="Rate", date_col="Start Date",
    slot_col="Booking Category", guests_col="Number of Guests",
    lead_col="Lead Days", competitor_col="Competitor_Price"
)
features_df = FeatureEngineer.process_dataframe(df_raw.copy())

trainer = MLTrainer()
report = trainer.train_and_select_champion(features_df)

print(f"\n--- TRAINING RESULTS ---")
print(f"R²: {report['metrics']['r2']*100:.2f}%")
print(f"MAE: ₹{report['metrics']['mae']:.0f}")
print(f"RMSE: ₹{report['metrics']['rmse']:.0f}")
