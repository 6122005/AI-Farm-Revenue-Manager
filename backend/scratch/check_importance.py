import joblib
from pathlib import Path
import pandas as pd

model_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/models_store/champion_model.joblib")
if not model_path.exists():
    print("No model found!")
    exit()

artifact = joblib.load(model_path)
model = artifact["model"]["base_model"]
features = artifact["features"]

importances = model.feature_importances_
feat_imp = pd.DataFrame({"Feature": features, "Importance": importances})
feat_imp = feat_imp.sort_values(by="Importance", ascending=False)

print("=== TOP 25 FEATURE IMPORTANCES ===")
print(feat_imp.head(25).to_string(index=False))

print("\n=== METRICS ===")
for k, v in artifact.get("metrics", {}).items():
    print(f"{k.upper()}: {v}")

