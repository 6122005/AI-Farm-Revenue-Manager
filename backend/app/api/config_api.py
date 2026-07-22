import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.db_models import SlotRule, ModelRunMetric
from app.models.schemas import SlotRuleSchema, ModelMetricResponse
from app.config import DEFAULT_COMMERCIAL_SLOTS

router = APIRouter(prefix="/api", tags=["Config & Model Info"])

@router.get("/slots")
async def get_commercial_slots(db: Session = Depends(get_db)):
    """
    Returns active Commercial Slot Engine configurations.
    """
    rules = db.query(SlotRule).all()
    if not rules:
        # Seed default rules
        for s in DEFAULT_COMMERCIAL_SLOTS:
            r = SlotRule(
                code=s["code"],
                name=s["name"],
                min_hours=s["min_hours"],
                max_hours=s["max_hours"],
                max_guests=s["max_guests"],
                description=s["description"]
            )
            db.add(r)
        db.commit()
        rules = db.query(SlotRule).all()

    return [
        {
            "code": r.code,
            "name": r.name,
            "min_hours": r.min_hours,
            "max_hours": r.max_hours,
            "max_guests": r.max_guests,
            "description": r.description,
            "base_multiplier": r.base_multiplier,
            "is_active": r.is_active
        } for r in rules
    ]

@router.get("/model-info", response_model=List[ModelMetricResponse])
async def get_model_metrics(db: Session = Depends(get_db)):
    """
    Returns validation performance metrics (R2, MAE, RMSE, MAPE) for trained algorithms.
    """
    metrics = db.query(ModelRunMetric).order_by(ModelRunMetric.r2_score.desc()).all()
    res = []
    for m in metrics:
        feat_imp = None
        if m.feature_importances:
            try:
                feat_imp = json.loads(m.feature_importances)
            except Exception:
                pass

        res.append({
            "model_name": m.model_name,
            "r2_score": m.r2_score,
            "mae": m.mae,
            "rmse": m.rmse,
            "mape": m.mape,
            "is_champion": m.is_champion,
            "trained_at": m.trained_at,
            "feature_importances": feat_imp
        })
    return res
