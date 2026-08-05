import pandas as pd
from datetime import datetime
from pathlib import Path

from app.database import engine, Base, SessionLocal
from app.models.db_models import PredictionLog

Base.metadata.create_all(bind=engine)

db = SessionLocal()
db.query(PredictionLog).delete()
db.commit()

from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.shadow_validator import ShadowValidator

def run_replay():
    print("🚀 Starting Historical Replay Engine...")
    
    df = DataPipeline.process_with_explicit_mapping(
        file_path=Path("data/Farm_Booking_Data.xlsx"),
        date_col="booking_date",
        slot_col="commercial_slot",
        price_col="selling_price",
        guests_col="person_count",
        lead_col="lead_days",
        competitor_col="competitor_price"
    )
    
    df = df.sort_values(by="booking_date")
    
    print(f"Loaded {len(df)} historical bookings for replay.")
    
    success_count = 0
    
    for idx, row in df.iterrows():
        b_date = row["booking_date"]
        slot = row["commercial_slot"]
        guests = int(row["person_count"])
        lead = int(row.get("lead_days", 7))
        actual_price = float(row["selling_price"])
        
        req = {
            "start_datetime": f"{b_date} 10:00",
            "end_datetime": f"{b_date} 22:00",
            "booking_date": b_date,
            "commercial_slot": slot,
            "person_count": guests,
            "lead_days": lead,
            "competitor_price": 0.0,
            "skip_consistency_check": False
        }
        
        try:
            res = prediction_engine.predict(req)
            
            log_entry = PredictionLog(
                booking_date=res.booking_date,
                booking_created_date=None,
                arrival_date=res.start_datetime.split(" ")[0] if res.start_datetime else None,
                month=int(res.booking_date.split("-")[1]) if res.booking_date and len(res.booking_date.split("-"))>1 else 1,
                is_weekend=res.is_weekend,
                is_festival=bool(res.festival_name and "Festival" in res.festival_name),
                is_vacation=False,
                commercial_slot=res.commercial_slot,
                person_count=res.person_count,
                lead_days=res.lead_days,
                shadow_ml_price=res.shadow_ml_price,
                rag_median_price=res.rag_median_price,
                final_price=res.recommended_price,
                model_version=res.champion_model,
                prediction_confidence=res.confidence_score,
                validation_status="PENDING"
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            log_entry.actual_selling_price = actual_price
            log_entry.booking_status = "Booked"
            log_entry.booking_time = datetime.utcnow()
            
            log_entry.abs_error_rag = abs(log_entry.rag_median_price - actual_price)
            log_entry.abs_error_ml = abs(log_entry.shadow_ml_price - actual_price)
            
            if log_entry.abs_error_ml < log_entry.abs_error_rag:
                log_entry.winning_model = "ML"
            elif log_entry.abs_error_ml > log_entry.abs_error_rag:
                log_entry.winning_model = "RAG"
            else:
                log_entry.winning_model = "TIE"
                
            log_entry.validation_status = "VALIDATED"
            db.commit()
            success_count += 1
                
        except Exception as e:
            print(f"Skipping row {idx} due to error: {e}")
            db.rollback()
            
    print(f"✅ Replayed {success_count} bookings.")
    
    print("📊 Generating Enterprise Validation Suite...")
    ShadowValidator.generate_validation_suite()
    print("✨ Process Complete. Check validation_report.md and CSV deliverables.")

if __name__ == "__main__":
    run_replay()
