import sys
from pathlib import Path
import pandas as pd

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.data_pipeline import DataPipeline

excel_path = backend_dir / "data" / "Farm_Booking_Data_new.xlsx"
xl = pd.ExcelFile(excel_path)
print("Sheet names:", xl.sheet_names)

df_clean = DataPipeline.load_and_process_file(excel_path)
print("DataPipeline processed shape:", df_clean.shape)
print("DataPipeline columns:", df_clean.columns.tolist())

# Let's inspect raw sheet with bookings
for name in xl.sheet_names:
    df_s = pd.read_excel(excel_path, sheet_name=name)
    print(f"Sheet '{name}' shape:", df_s.shape)
