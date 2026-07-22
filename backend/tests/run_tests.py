import os
import sys

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app
from app.services.slot_engine import slot_engine
from app.services.feature_engineering import FeatureEngineer
from app.services.data_pipeline import DataPipeline, CLEAN_DATA_PATH
from app.services.ml_trainer import MLTrainer

def run_all_tests():
    print("🚀 Starting Backend Unit Tests...")
    client = TestClient(app)

    # 1. Root Test
    res = client.get("/")
    assert res.status_code == 200
    print("✅ Root API Test Passed")

    # 2. Slot Engine Test
    assert slot_engine.map_duration_to_slot(5.0, 2) in ["COUPLE_DAY", "COUPLE_NIGHT", "COUPLE_SLOT"]
    assert slot_engine.map_duration_to_slot(10.0, 8) == "12H_DAY"
    assert slot_engine.map_duration_to_slot(24.0, 10) == "24H_DAY"
    assert slot_engine.classify_by_datetimes("2025-10-22 19:00", "2025-10-23 07:00", 2) == "COUPLE_NIGHT"
    print("✅ Commercial Slot Engine Test Passed")

    # 3. Default Empty Dashboard State Test
    if CLEAN_DATA_PATH.exists():
        CLEAN_DATA_PATH.unlink()

    dash_empty = client.get("/api/dashboard")
    assert dash_empty.status_code == 200
    d_empty = dash_empty.json()
    assert d_empty["has_data"] == False
    assert d_empty["total_revenue"] == 0.0
    print("✅ Default Empty Dashboard State Verified")

    # 4. User Upload Seed Data & ML Training Test
    df = DataPipeline.generate_synthetic_historical_data(100)
    df_enriched = FeatureEngineer.process_dataframe(df)
    df_enriched.to_csv(CLEAN_DATA_PATH, index=False)
    DataPipeline.sync_to_db(df_enriched)
    artifact = MLTrainer.train_and_select_champion(df_enriched)
    print(f"✅ User Data Processing & ML Champion Training Passed! Champion: {artifact['champion_name']}")

    # 5. Predict API Test with Start/End Datetime
    payload = {
        "start_datetime": "2025-10-22 19:00",
        "end_datetime": "2025-10-23 18:00",
        "commercial_slot": "24H_NIGHT",
        "person_count": 10,
        "competitor_price": 6500.0
    }
    pred_res = client.post("/api/predict", json=payload)
    assert pred_res.status_code == 200
    data = pred_res.json()
    assert "recommended_price" in data
    assert data["recommended_price"] > 0
    assert "duration_hours" in data
    assert data["duration_hours"] == 23.0
    assert "festival_name" in data
    assert "is_weekend" in data
    print(f"✅ Predict API with Datetime Range Passed! Rec Price: ₹{data.get('recommended_price')} | Duration: {data.get('duration_hours')} Hours | Festival: {data.get('festival_name')}")

    # 6. Dashboard Analytics with User Upload Data Test
    dash_full = client.get("/api/dashboard")
    assert dash_full.status_code == 200
    d_full = dash_full.json()
    assert d_full["has_data"] == True
    assert d_full["total_revenue"] > 0
    print(f"✅ User Data Dashboard Analytics Test Passed! Revenue: ₹{d_full['total_revenue']:,.2f}")

    # 7. Feedback Audit Loop Test
    fb_payload = {
        "booking_date": "2025-10-22",
        "commercial_slot": "24H_NIGHT",
        "person_count": 10,
        "lead_days": 15,
        "suggested_price": 16000.0,
        "action": "ACCEPT"
    }
    fb_res = client.post("/api/feedback", json=fb_payload)
    assert fb_res.status_code == 200
    print("✅ Feedback Audit Loop Test Passed!")

    print("\n🎉 ALL BACKEND UNIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_all_tests()
