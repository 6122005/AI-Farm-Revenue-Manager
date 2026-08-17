import re
from pathlib import Path

fpath = Path("backend/app/services/ml_trainer.py")
code = fpath.read_text()

# Reintroduce XGBoost Monotonic Constraints
constraint_code = """
        # MONOTONIC CONSTRAINTS
        # We mathematically force the model to respect: 
        # 1. More guests >= More money
        # 2. Higher duration ratio >= More money
        monotone_constraints = {}
        for idx, col in enumerate(features):
            if "person_count" in col or "duration_ratio" in col:
                monotone_constraints[col] = 1
            else:
                monotone_constraints[col] = 0
                
        model_B = XGBRegressor(
            n_estimators=100, 
            max_depth=4, 
            learning_rate=0.05, 
            random_state=42,
            monotone_constraints=monotone_constraints
        )
"""

code = re.sub(
    r"model_B = XGBRegressor\(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42\)",
    constraint_code.strip(),
    code
)

fpath.write_text(code)
print("Constraints added.")
