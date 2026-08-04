import pandas as pd
from app.services.feature_engineering import FeatureEngineer
from app.services.prediction_engine import prediction_engine
import traceback

# Override the method to just execute its body without try-except
import inspect
src = inspect.getsource(FeatureEngineer.calculate_group_averages)
# Remove the try/except from the source string
src = src.replace("        try:\n", "")
src = src.replace("        except Exception as e:\n", "")
src = src.replace("            print(f\"⚠️ Error saving group averages: {e}\")\n", "")
src = src.replace("            return {}\n", "")

# The indentation will be messed up, so let's just edit the file directly using python script.

