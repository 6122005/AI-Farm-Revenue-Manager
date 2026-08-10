import urllib.request
import json

url = "http://127.0.0.1:8000/api/predict"
payload = {
    "start_datetime": "2028-05-13 19:00",
    "end_datetime": "2028-05-14 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "competitor_price": 0
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            data = json.loads(response.read().decode('utf-8'))
            print("✅ Localhost API Test Successful!")
            print(f"Requested Date: {payload['start_datetime']} (May 2028 Weekend)")
            print(f"Returned Final Price: ₹{data['revenue_optimized_price']}")
            print(f"RAG Baseline Price: ₹{data['rag_median_price']}")
            print("Price Breakdown:")
            for factor in data['price_factors']:
                print(f" - {factor['factor']}: {factor['impact_amount']} ({factor['description']})")
        else:
            print(f"❌ API Error: {response.status}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
