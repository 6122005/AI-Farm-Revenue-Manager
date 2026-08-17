import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.ml_trainer import MLTrainer
from pathlib import Path

data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

target_col = "selling_price"
train_df = df_feat[df_feat[target_col] > 0].copy()
y = train_df[target_col]

trainer = MLTrainer()
trainer.prepare_features(train_df)
X = train_df[trainer.features]
trainer.model.fit(X, y)
preds = trainer.model.predict(X)

train_df["predicted"] = preds
train_df["error"] = train_df["predicted"] - train_df["selling_price"]
train_df["abs_error"] = train_df["error"].abs()

print("\n--- TOP 20 BIGGEST ERRORS ---")
cols_to_show = ["booking_date", "commercial_slot", "person_count", "duration_hours", "selling_price", "predicted", "error", "abs_error"]
print(train_df.sort_values(by="abs_error", ascending=False).head(20)[cols_to_show].to_string())

print("\n--- ERROR BY CATEGORY ---")
print(train_df.groupby("commercial_slot")["abs_error"].mean().sort_values(ascending=False))

print("\n--- ERROR BY PERSON COUNT ---")
print(train_df.groupby(pd.cut(train_df["person_count"], bins=[0,4,10,20,100]))["abs_error"].mean())

