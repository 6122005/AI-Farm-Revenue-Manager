import json
from app.services.prediction_engine import PredictionEngine

engine = PredictionEngine()

# We test with exactly 4 guests and 15 lead days to isolate the festival effect
base_req = {
    "person_count": 4,
    "lead_days": 15
}

test_cases = [
    {
        "name": "Scenario 1: 24H Day touching Makara Sankranti (14th Jan)",
        "start_datetime": "2027-01-13 10:00",
        "end_datetime": "2027-01-14 10:00",
        "commercial_slot": "24H Day",
        "expected_festival": "Makara Sankranti"
    },
    {
        "name": "Scenario 2: 12H Night touching Makara Sankranti",
        "start_datetime": "2027-01-13 19:00",
        "end_datetime": "2027-01-14 07:00",
        "commercial_slot": "12H Night",
        "expected_festival": "Makara Sankranti"
    },
    {
        "name": "Scenario 3: 12H Day strictly on 13th (NO overlap)",
        "start_datetime": "2027-01-13 10:00",
        "end_datetime": "2027-01-13 22:00",
        "commercial_slot": "12H Day",
        "expected_festival": "None"
    },
    {
        "name": "Scenario 4: 24H Night touching Holi (22nd March)",
        "start_datetime": "2027-03-21 19:00",
        "end_datetime": "2027-03-22 19:00",
        "commercial_slot": "24H Night",
        "expected_festival": "Holi"
    },
    {
        "name": "Scenario 5: 12H Day strictly on 21st March (NO overlap)",
        "start_datetime": "2027-03-21 10:00",
        "end_datetime": "2027-03-21 22:00",
        "commercial_slot": "12H Day",
        "expected_festival": "None"
    }
]

print("Starting Festival Overlap Tests...\n" + "-"*40)
for t in test_cases:
    req = base_req.copy()
    req["start_datetime"] = t["start_datetime"]
    req["end_datetime"] = t["end_datetime"]
    req["commercial_slot"] = t["commercial_slot"]
    
    res = engine.predict(req)
    
    fest_applied = False
    fest_reason = ""
    for factor in res.price_factors:
        if "touches festival" in factor.description or "matches festival" in factor.description:
            fest_applied = True
            fest_reason = factor.description
            
    success = False
    if t["expected_festival"] == "None" and not fest_applied:
        success = True
    elif t["expected_festival"] != "None" and t["expected_festival"] in fest_reason:
        success = True
        
    print(f"Test: {t['name']}")
    print(f"Time: {t['start_datetime']} to {t['end_datetime']}")
    print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
    if fest_applied:
        print(f"Applied: {fest_reason}")
    else:
        print("Applied: No festival premium applied.")
    print("-" * 40)
