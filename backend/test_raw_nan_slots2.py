import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

from app.services.data_pipeline import DataPipeline

# Let's count the inferred slots properly
mapped = DataPipeline.process_with_explicit_mapping(
    file_path=path,
    price_col="Rate",
    date_col="Start Date",
    slot_col="Booking Category"
)

print(mapped["duration_hours"].value_counts(dropna=False))
