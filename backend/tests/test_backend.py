import os
os.environ["TESTING"] = "1"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.slot_engine import slot_engine
from app.services.feature_engineering import FeatureEngineer
from app.services.prediction_engine import prediction_engine

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_slot_engine_mapping():
    assert slot_engine.classify_booking(12, 5.0) == "12H Day"
    assert slot_engine.classify_booking(19, 5.0) == "12H Night"
    assert slot_engine.classify_booking(12, 24.0) == "24H Day"
    assert slot_engine.classify_booking(19, 24.0) == "24H Night"

def test_feature_engineer():
    feats = FeatureEngineer.extract_features_from_dict({
        "booking_date": "2026-08-15",
        "person_count": 8,
        "lead_days": 5,
        "slot_type": "12H Day"
    })
    assert feats["month"] == 8
    assert feats["is_weekend"] == 1
    assert feats["person_count"] == 8
    assert "demand_score" in feats

def test_predict_api():
    payload = {
        "booking_date": "2026-08-15",
        "slot_type": "12H Day",
        "person_count": 8,
        "lead_days": 5,
        "competitor_price": 9500.0
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_price" in data
    assert data["recommended_price"] > 0
    assert "price_factors" in data
    assert "similar_bookings" in data
    assert "weather" in data

def test_dashboard_api():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "monthly_revenue" in data
    assert "demand_heatmap" in data

def test_validation_dashboard_api():
    response = client.get("/api/dashboard/validation")
    assert response.status_code == 200
    data = response.json()
    assert "ai_avg_price" in data
    assert "owner_avg_price" in data
    assert "override_rate" in data
    assert "drift_detected" in data
    assert "retraining_recommendation" in data

def test_slots_api():
    response = client.get("/api/slots")
    assert response.status_code == 200
    assert len(response.json()) >= 4

def test_feedback_api():
    payload = {
        "booking_date": "2026-08-15",
        "slot_type": "12H Day",
        "person_count": 8,
        "lead_days": 5,
        "suggested_price": 9800.0,
        "action": "OVERRIDE",
        "override_price": 10500.0,
        "reason": "High demand weekend during peak monsoon"
    }
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
