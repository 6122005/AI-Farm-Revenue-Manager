from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.db_models import OwnerFeedback
from app.models.schemas import OwnerFeedbackCreate

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

@router.post("")
async def log_owner_feedback(fb: OwnerFeedbackCreate, db: Session = Depends(get_db)):
    """
    Logs owner feedback (ACCEPT, OVERRIDE, REJECT) for a price prediction.
    Enables future retraining pipelines to learn from owner pricing decisions.
    """
    try:
        feedback_rec = OwnerFeedback(
            booking_date=fb.booking_date,
            commercial_slot=fb.commercial_slot,
            person_count=fb.person_count,
            lead_days=fb.lead_days,
            suggested_price=fb.suggested_price,
            action=fb.action.upper(),
            override_price=fb.override_price,
            reason=fb.reason
        )
        db.add(feedback_rec)
        db.commit()
        db.refresh(feedback_rec)

        return {
            "status": "success",
            "message": f"Owner decision '{fb.action}' logged successfully.",
            "feedback_id": feedback_rec.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log feedback: {str(e)}")

@router.get("/history")
async def get_feedback_history(db: Session = Depends(get_db)):
    """
    Returns audit trail of past owner decisions.
    """
    records = db.query(OwnerFeedback).order_by(OwnerFeedback.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "booking_date": r.booking_date,
            "commercial_slot": r.commercial_slot,
            "person_count": r.person_count,
            "lead_days": r.lead_days,
            "suggested_price": r.suggested_price,
            "action": r.action,
            "override_price": r.override_price,
            "reason": r.reason,
            "created_at": r.created_at.isoformat()
        } for r in records
    ]
