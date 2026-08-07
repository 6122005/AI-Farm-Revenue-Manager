import pandas as pd
from app.services.prediction_engine import PredictionEngine
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

engine = PredictionEngine()

# Read Sheet4 to get the festivals
data_path = "data/Farm_Booking_Data_new.xlsx"
df_fest = pd.read_excel(data_path, sheet_name="Sheet4")

artifact_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/f85b134a-8677-463b-ab33-33093b97a4f8/2026_festival_prices.md"

with open(artifact_path, "w") as f:
    f.write("# Future Festival Pricing Predictions (2026-2027)\n\n")
    f.write("This report predicts the **24H Night** slot for **10 Guests** (3 Lead Days) for all upcoming festivals based on the exact multipliers defined in the Excel `Sheet4`.\n\n")
    f.write("| Date | Festival Name | Day Type | Excel Multiplier | Final Predicted Price |\n")
    f.write("| :--- | :--- | :--- | :---: | :--- |\n")
    
    # Sort by date
    df_fest['Date'] = pd.to_datetime(df_fest['Date'], errors='coerce')
    df_fest = df_fest.dropna(subset=['Date']).sort_values(by='Date')
    
    for idx, row in df_fest.iterrows():
        try:
            dt_obj = row['Date']
            
            # Only future dates (2026 onwards)
            if dt_obj.year < 2026:
                continue
                
            date_str = dt_obj.strftime("%Y-%m-%d")
            name = str(row.get('Festival_Name', 'Holiday'))
            multiplier = float(row.get('multiplier', 1.0))
            if pd.isna(multiplier):
                multiplier = 1.0
                
            # Determine if weekend
            day_of_week = dt_obj.strftime("%A")
            is_weekend = day_of_week in ["Saturday", "Sunday"]
            day_type = "Weekend" if is_weekend else "Weekday"
            
            start_datetime = f"{date_str} 19:00"
            end_dt = dt_obj + pd.Timedelta(days=1)
            end_datetime = f"{end_dt.strftime('%Y-%m-%d')} 19:00"
            
            req = {
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "commercial_slot": "24H Night",
                "person_count": 10,
                "lead_days": 3,
                "skip_festival": False
            }
            
            res = engine.predict(req)
            
            f.write(f"| {date_str} ({day_of_week}) | {name} | {day_type} | {multiplier}x | **₹{res.recommended_price:,.0f}** |\n")
        except Exception as e:
            print(f"Error on row {idx}: {e}")

print("Done")
