from fastapi import APIRouter, HTTPException
from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.prediction_engine import prediction_engine
from app.services.weather_service import weather_service

router = APIRouter(prefix="/api/predict", tags=["Prediction"])

@router.post("", response_model=PredictionResponse)
async def get_price_prediction(req: PredictionRequest):
    """
    Predicts optimal commercial slot selling price for a future request date.
    Integrates OpenWeather forecast, XAI factor waterfall, and similar historical booking evidence.
    """
    try:
        res = prediction_engine.predict(req.dict())
        
        # Log to Shadow DB
        from app.database import SessionLocal
        from app.models.db_models import PredictionLog
        
        db = SessionLocal()
        try:
            log_entry = PredictionLog(
                booking_date=res.booking_date,
                booking_created_date=None,  # Or parse from lead_days if needed
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
            res.prediction_id = log_entry.id
        except Exception as e:
            print(f"Error logging prediction: {e}")
        finally:
            db.close()
            
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

from app.models.schemas import OutcomeRequest
from datetime import datetime

@router.post("/outcome")
async def register_booking_outcome(req: OutcomeRequest):
    """
    Registers the actual outcome of a prediction. Updates the shadow log and calculates errors.
    """
    from app.database import SessionLocal
    from app.models.db_models import PredictionLog
    
    db = SessionLocal()
    try:
        log_entry = db.query(PredictionLog).filter(PredictionLog.id == req.prediction_id).first()
        if not log_entry:
            raise HTTPException(status_code=404, detail="Prediction ID not found")
            
        log_entry.actual_selling_price = req.actual_selling_price
        log_entry.booking_status = req.booking_status
        log_entry.negotiated_price = req.negotiated_price
        log_entry.discount_given = req.discount_given
        log_entry.booking_time = datetime.utcnow()
        
        # Calculate Errors
        log_entry.abs_error_rag = abs(log_entry.rag_median_price - req.actual_selling_price)
        log_entry.abs_error_ml = abs(log_entry.shadow_ml_price - req.actual_selling_price)
        
        if log_entry.abs_error_ml < log_entry.abs_error_rag:
            log_entry.winning_model = "ML"
        elif log_entry.abs_error_ml > log_entry.abs_error_rag:
            log_entry.winning_model = "RAG"
        else:
            log_entry.winning_model = "TIE"
            
        log_entry.validation_status = "VALIDATED"
        
        db.commit()
        return {"status": "success", "message": f"Outcome registered for Prediction ID {req.prediction_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register outcome: {str(e)}")
    finally:
        db.close()

@router.get("/weather-preview")
async def get_weather_preview(booking_date: str = "2025-10-22"):
    """
    Returns weather forecast preview for the selected booking date.
    """
    try:
        return weather_service.get_forecast(booking_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather forecast: {str(e)}")

@router.get("/audit")
async def get_prediction_audit(row_index: int = 0):
    """
    Returns complete forensic analysis for a specific booking by row index.
    """
    try:
        return prediction_engine.audit_prediction(row_index)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prediction audit: {str(e)}")
