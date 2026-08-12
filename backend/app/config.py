import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models_store"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/farmhouse_rm.db")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_CITY = os.getenv("OPENWEATHER_CITY", "Surat,IN")
ENABLE_EXPECTED_REVENUE_OPTIMIZATION = os.getenv("ENABLE_EXPECTED_REVENUE_OPTIMIZATION", "False").lower() in ("true", "1", "t")


# Commercial Slot definitions with exact timing windows
DEFAULT_COMMERCIAL_SLOTS = [
    {
        "code": "12H Day",
        "name": "12 Hour Day",
        "min_hours": 1.0,
        "max_hours": 13.0,
        "max_guests": 50,
        "description": "Daytime slot"
    },
    {
        "code": "12H Night",
        "name": "12 Hour Night",
        "min_hours": 1.0,
        "max_hours": 13.0,
        "max_guests": 50,
        "description": "Nighttime slot"
    },
    {
        "code": "24H Day",
        "name": "24 Hour Day",
        "min_hours": 13.1,
        "max_hours": 24.0,
        "max_guests": 50,
        "description": "Full 24-hour day starting in the morning"
    },
    {
        "code": "24H Night",
        "name": "24 Hour Night",
        "min_hours": 13.1,
        "max_hours": 24.0,
        "max_guests": 50,
        "description": "Full 24-hour night starting in the evening"
    }
]
