import re

with open("historical_replay_engine.py", "r") as f:
    content = f.read()

old_block = """        try:
            # 1. Prediction (This internally logs to PredictionLog as PENDING)
            res = prediction_engine.predict(req)
            
            # 2. Outcome Injection
            log_id = res.prediction_id
            if not log_id:
                # If for some reason predict() failed to return ID
                continue
                
            log_entry = db.query(PredictionLog).filter(PredictionLog.id == log_id).first()
            if log_entry:
                log_entry.actual_selling_price = actual_price
                log_entry.booking_status = "Booked"
                log_entry.booking_time = datetime.utcnow()"""

new_block = """        try:
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
            
            if log_entry:
                log_entry.actual_selling_price = actual_price
                log_entry.booking_status = "Booked"
                log_entry.booking_time = datetime.utcnow()"""

content = content.replace(old_block, new_block)

with open("historical_replay_engine.py", "w") as f:
    f.write(content)

