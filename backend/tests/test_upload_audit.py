import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from app.main import app
from app.services.data_pipeline import SAMPLE_EXCEL_PATH, DataPipeline

def test_full_upload_transparency_audit():
    print("\n🔍 Running Upload Transparency Audit Test...")
    client = TestClient(app)

    # Generate sample Excel file
    DataPipeline.generate_synthetic_historical_data(150)
    assert SAMPLE_EXCEL_PATH.exists()

    with open(SAMPLE_EXCEL_PATH, "rb") as f:
        response = client.post("/api/upload/preview", files={"file": ("Farm_Booking_Data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

    assert response.status_code == 200
    p_data = response.json()
    temp_filename = p_data["temp_filename"]
    print(f"Preview successful. Temp filename: {temp_filename}")

    # Validate mapping
    mapping_payload = {
        "temp_filename": temp_filename,
        "price_col": "selling_price",
        "date_col": "booking_date",
        "slot_col": "commercial_slot",
        "guests_col": "person_count",
        "lead_col": "lead_days",
        "competitor_col": "competitor_price"
    }

    val_res = client.post("/api/upload/validate", json=mapping_payload)
    assert val_res.status_code == 200
    print("Validation report generated.")

    # Confirm and train (triggers full 17-item transparency audit & timestamp check)
    train_res = client.post("/api/upload/confirm-and-train", json=mapping_payload)
    assert train_res.status_code == 200
    t_data = train_res.json()
    proof = t_data["audit_proof"]

    assert proof["uploaded_filename"] == temp_filename
    assert "uploaded_file_path" in proof
    assert proof["raw_rows_count"] > 0
    assert len(proof["detected_columns"]) > 0
    assert proof["target_column_selected"] == "selling_price"
    assert len(proof["first_10_target_prices"]) == 10
    assert proof["average_booking_price"] > 0
    assert proof["minimum_booking_price"] > 0
    assert proof["maximum_booking_price"] > 0
    assert len(proof["slot_distribution"]) > 0
    assert proof["cleaned_rows_count"] > 0
    assert proof["training_rows_count"] > 0
    assert "training_started_at" in proof
    assert "training_completed_at" in proof
    assert "saved_model_filename" in proof
    assert "saved_model_path" in proof
    assert "model_creation_timestamp" in proof
    assert "loaded_prediction_model_path" in proof
    assert "loaded_prediction_model_timestamp" in proof
    assert proof["timestamp_match_verified"] == True

    print(f"✅ Full 17-Item Upload Transparency Audit Test Passed!")
    print(f"Verified Model Creation Timestamp: '{proof['model_creation_timestamp']}'")
    print(f"Verified Loaded Model Timestamp: '{proof['loaded_prediction_model_timestamp']}'")

    # Now make a prediction request and verify model path + timestamp + historical row evidence
    pred_res = client.post("/api/predict", json={
        "start_datetime": "2025-10-22 19:00",
        "end_datetime": "2025-10-23 07:00",
        "commercial_slot": "12H_NIGHT",
        "person_count": 4
    })
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["model_path_used"] == proof["loaded_prediction_model_path"]
    assert pred_data["model_timestamp_used"] == proof["loaded_prediction_model_timestamp"]
    assert len(pred_data["contributing_historical_rows"]) > 0
    assert "historical_price_explanation" in pred_data
    print(f"✅ Prediction Traceability Verified! Model Path: {pred_data['model_path_used']}")

if __name__ == "__main__":
    test_full_upload_transparency_audit()
