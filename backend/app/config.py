import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models_store"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/farmhouse_rm.db")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY","")
OPENWEATHER_CITY = os.getenv("OPENWEATHER_CITY", "Lonavala")

# Commercial Slot definitions with exact timing windows
DEFAULT_COMMERCIAL_SLOTS = [
    {
        "code": "COUPLE_SLOT",
        "name": "Couple Special (2 Guests)",
        "min_hours": 12.0,
        "max_hours": 24.0,
        "max_guests": 2,
        "description": "Discounted couple slot (2 guests) with lower electricity & utility consumption"
    },
    {
        "code": "COUPLE_DAY",
        "name": "Couple Slot Day (7 AM to 7 PM)",
        "min_hours": 12.0,
        "max_hours": 12.0,
        "max_guests": 2,
        "description": "Daytime couple slot from 7:00 AM to 7:00 PM for 2 guests"
    },
    {
        "code": "COUPLE_NIGHT",
        "name": "Couple Slot Night (7 PM to 7 AM)",
        "min_hours": 12.0,
        "max_hours": 12.0,
        "max_guests": 2,
        "description": "Overnight couple slot from 7:00 PM to 7:00 AM for 2 guests"
    },
    {
        "code": "12H_DAY",
        "name": "12 Hour Day (7 AM to 7 PM)",
        "min_hours": 12.0,
        "max_hours": 12.0,
        "max_guests": 50,
        "description": "Daytime slot from 7:00 AM to 7:00 PM"
    },
    {
        "code": "12H_NIGHT",
        "name": "12 Hour Night (7 PM to 7 AM)",
        "min_hours": 12.0,
        "max_hours": 12.0,
        "max_guests": 50,
        "description": "Overnight slot from 7:00 PM to 7:00 AM (Next Day)"
    },
    {
        "code": "24H_DAY",
        "name": "24 Hour Day (7 AM to 7 AM)",
        "min_hours": 24.0,
        "max_hours": 24.0,
        "max_guests": 50,
        "description": "Full 24-hour stay starting 7:00 AM to 7:00 AM (Next Day)"
    },
    {
        "code": "24H_NIGHT",
        "name": "24 Hour Night (7 PM to 7 PM)",
        "min_hours": 24.0,
        "max_hours": 24.0,
        "max_guests": 50,
        "description": "Full 24-hour stay starting 7:00 PM to 7:00 PM (Next Day)"
    }
]
