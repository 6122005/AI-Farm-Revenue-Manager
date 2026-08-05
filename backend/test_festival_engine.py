import sys
import os
import pandas as pd
from datetime import datetime

# Adjust path to import backend modules
sys.path.append(os.path.abspath('.'))

from app.services.prediction_engine import prediction_engine

def run_tests():
    print("Running Festival Intelligence Engine Test...")
    
    # 1. Test Makar Sankranti overlap
    req_1 = {
        "booking_date": "2024-01-13",
        "commercial_slot": "12H Night",
        "duration_hours": 14,
        "person_count": 6,
        "lead_days": 10
    }
    
    print("\n--- Test 1: 13 Jan 6PM to 14 Jan 8AM ---")
    # Night slot will be parsed as starting at 18:00
    res_1 = prediction_engine.predict(req_1)
    
    explanation = res_1.get("festival_explanation", {})
    print(f"Festival Detected: {explanation.get('Festival Detected')}")
    print(f"Festival Name: {explanation.get('Festival Name')}")
    print(f"Overlap Hours: {explanation.get('Overlap Hours')}")
    print(f"Reason: {explanation.get('Reason')}")

    assert explanation.get('Festival Detected') is True, "Expected Makar Sankranti to be detected for Jan 13 night."
    assert explanation.get('Overlap Hours') == 14.0, f"Expected 14 hours of overlap, got {explanation.get('Overlap Hours')}"
    print("✅ Test 1 Passed!")
    
    
    # 2. Test Booking finishing just before window
    req_2 = {
        "booking_date": "2024-01-13",
        "commercial_slot": "12H Day", # 08:00 to 16:00 (8 hours)
        "duration_hours": 8,
        "person_count": 6,
        "lead_days": 10
    }
    
    print("\n--- Test 2: 13 Jan 8AM to 4PM (finishes before 5PM start) ---")
    res_2 = prediction_engine.predict(req_2)
    explanation_2 = res_2.get("festival_explanation", {})
    print(f"Festival Detected: {explanation_2.get('Festival Detected')}")
    print(f"Overlap Hours: {explanation_2.get('Overlap Hours')}")
    assert explanation_2.get('Festival Detected') is False, "Expected no festival detection."
    print("✅ Test 2 Passed!")

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()
