import pandas as pd
from app.services.prediction_engine import prediction_engine
import json

def analyze_feb_prediction():
    payload = {
        "booking_date": "2026-02-15",
        "duration_hours": 24.0,
        "person_count": 10,
        "slot_type": "24H Night",
        "weather_condition": "Clear",
        "temperature": 25.0,
        "rain_probability": 0.0,
        "humidity": 50.0,
        "wind_speed": 10.0,
        "cloud_cover": 0.0,
        "is_festival": False
    }
    
    # Run the prediction and capture the enriched features
    result = prediction_engine.predict(payload)
    
    print("\n--- FINAL PREDICTION RESULTS ---")
    print(f"Final Predicted Price: ₹{result['predicted_price']}")
    
    # We want to see what features went into the XGBoost model.
    # PredictionEngine logs out the enriched features internally if we call process_dataframe
    from app.services.feature_engineering import FeatureEngineer
    df_req = pd.DataFrame([payload])
    enriched_df = FeatureEngineer.process_dataframe(df_req)
    
    print("\n--- KEY MODEL FEATURES ---")
    print(f"slot_month_weekend_ratio_24H Night_2: {enriched_df['slot_month_weekend_ratio_24H Night_2'].values[0]}")
    print(f"base_group_average (seg_24H Night_2_1_trimmed_mean): {enriched_df.get('seg_24H Night_2_1_trimmed_mean', [0])[0]}")
    print(f"person_count: {enriched_df['person_count'].values[0]}")
    print(f"extra_guests: {enriched_df.get('extra_guests', [0])[0]}")
    
    # Also grab the raw historical average to show how it anchors it
    with open("data/group_averages.json", "r") as f:
        avgs = json.load(f)
    print(f"\nRaw Time-Decayed Group Average (4 Guests Base): ₹{avgs.get('slot_month_weekend_24H Night_2_1', 0):.2f}")
    
if __name__ == "__main__":
    analyze_feb_prediction()
