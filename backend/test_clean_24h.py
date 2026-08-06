from app.services.prediction_engine import prediction_engine
df = prediction_engine.get_clean_data()
print("Clean commercial slots count:")
print(df['commercial_slot'].value_counts(dropna=False))
