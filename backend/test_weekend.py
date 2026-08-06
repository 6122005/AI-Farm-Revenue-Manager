import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.config import DATA_DIR

path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

mapped = DataPipeline.process_with_explicit_mapping(
    file_path=path,
    price_col="Rate",
    date_col="Start Date",
    slot_col="Booking Category"
)

print(mapped[['date', 'commercial_slot', 'day_of_week', 'is_weekend']].head(20))
