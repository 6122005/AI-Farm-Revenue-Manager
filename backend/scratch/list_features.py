import joblib
from pathlib import Path

model_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/models_store/champion_model.joblib")
if not model_path.exists(): exit("No model")

artifact = joblib.load(model_path)
features = artifact["features"]
print("Total Features:", len(features))
for i, f in enumerate(features, 1):
    print(f"{i}. {f}")
