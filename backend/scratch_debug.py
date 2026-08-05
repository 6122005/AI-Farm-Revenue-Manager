import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.services.prediction_engine import prediction_engine
from datetime import datetime
import json

req = {
    "start_datetime": "2026-10-20 07:00",
    "end_datetime": "2026-10-21 07:00",
    "commercial_slot": "24 Hour Day",
    "person_count": 10,
    "lead_days": 75
}

try:
    res = prediction_engine.predict(req)
    print(res.model_dump_json(indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()

