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
    assert slot_engine.map_duration_to_slot(5.0, 2) == "COUPLE_SLOT"
    assert slot_engine.map_duration_to_slot(5.0, 6) == "6H_SLOT"
    assert slot_engine.map_duration_to_slot(10.0, 8) == "12H_SLOT"
    assert slot_engine.map_duration_to_slot(24.0, 10) == "24H_FULL_SLOT"

def test_feature_engineer():
    feats = FeatureEngineer.extract_features_from_dict({
        "booking_date": "2026-08-15",
        "person_count": 8,
        "lead_days": 5,
        "commercial_slot": "12H_SLOT"
    })
    assert feats["month"] == 8
    assert feats["is_weekend"] == 1
    assert feats["person_count"] == 8
    assert "demand_score" in feats

def test_predict_api():
    payload = {
        "booking_date": "2026-08-15",
        "commercial_slot": "12H_SLOT",
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

def test_slots_api():
    response = client.get("/api/slots")
    assert response.status_code == 200
    assert len(response.json()) >= 5

def test_feedback_api():
    payload = {
        "booking_date": "2026-08-15",
        "commercial_slot": "12H_SLOT",
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
