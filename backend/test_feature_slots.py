import pandas as pd
from app.services.prediction_engine import prediction_engine
df = prediction_engine.get_clean_data()
print("Clean slots count:")
print(df['commercial_slot'].value_counts(dropna=False))

# Show me rows 252, 253, 515, 516
for idx in [252, 253, 515, 516]:
    if idx in df.index:
        row = df.loc[idx]
        print(f"Row {idx}: slot={row['commercial_slot']}, price={row['selling_price']}")
    else:
        print(f"Row {idx} not in clean df!")
