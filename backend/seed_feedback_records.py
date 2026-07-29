import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.database import SessionLocal
from app.models.db_models import OwnerFeedback
from datetime import datetime, timedelta
import random

def seed_feedback():
    db = SessionLocal()
    # Clear existing feedback to make it clean
    db.query(OwnerFeedback).delete()
    
    slots = ["12H Day", "12H Night", "24H Day", "24H Night"]
    reasons = [
        "Special customer discount",
        "Peak weekend demand rush",
        "Competitor matching rate",
        "Included catering adjustment",
        "Custom decoration premium"
    ]
    
    feedbacks = []
    base_date = datetime(2026, 6, 20)
    
    # Generate 25 records
    for i in range(25):
        b_date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        slot = random.choice(slots)
        guests = random.choice([2, 4, 8, 10, 15])
        lead = random.choice([3, 7, 10, 14])
        
        suggested = float(random.choice([2500, 3000, 4500, 5000, 6500, 8000]))
        
        # Action distribution: 18 ACCEPT (72%), 5 OVERRIDE (20%), 2 REJECT (8%)
        if i < 18:
            action = "ACCEPT"
            override_price = None
            reason = None
        elif i < 23:
            action = "OVERRIDE"
            # Overrides are usually higher or lower slightly
            override_price = suggested + float(random.choice([-500, 500, 1000, 1500]))
            reason = random.choice(reasons)
        else:
            action = "REJECT"
            override_price = None
            reason = "Customer cancelled search"
            
        fb = OwnerFeedback(
            booking_date=b_date,
            slot_type=slot,
            person_count=guests,
            lead_days=lead,
            suggested_price=suggested,
            action=action,
            override_price=override_price,
            reason=reason,
            created_at=datetime.utcnow() - timedelta(days=25 - i)
        )
        feedbacks.append(fb)
        
    db.bulk_save_objects(feedbacks)
    db.commit()
    db.close()
    print("🎉 Seeded 25 realistic feedback records in the database.")

if __name__ == "__main__":
    seed_feedback()
