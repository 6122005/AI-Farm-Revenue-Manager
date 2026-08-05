import joblib
model = joblib.load("models_store/champion_model.joblib")
print(type(model))
if isinstance(model, dict):
    print("Keys:", model.keys())
