import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

nan_rows = df[df['Booking Category'].isna()]
print("Number of NaN Booking Categories:", len(nan_rows))
print("Duration value counts for NaN rows:", nan_rows['Duration'].value_counts(dropna=False))

# Let's run the pipeline extraction to see how many 24H Night and 24H Day slots we ACTUALLY GET from inference!
from app.services.data_pipeline import DataPipeline
mapped_df = DataPipeline.load_raw_dataframe(path)

# Let's count the inferred slots properly
mapped = DataPipeline.process_with_explicit_mapping(
    file_path=path,
    price_col="Rate",
    date_col="Start Date",
    slot_col="Booking Category"
)
print("After pipeline processing, commercial slots count:")
print(mapped['commercial_slot'].value_counts(dropna=False))

print("\nLet's check the average price for 24H Night in the processed data!")
s_df = mapped[mapped['commercial_slot'] == "24H Night"]
print(f"24H Night Count: {len(s_df)}")
print(f"24H Night Avg Price: {s_df['selling_price'].mean()}")
print(f"24H Night Median Price: {s_df['selling_price'].median()}")
