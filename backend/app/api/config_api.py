import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.db_models import SlotRule, ModelRunMetric, LeadDaysRule, SystemSetting
from app.models.schemas import SlotRuleSchema, ModelMetricResponse, LeadDaysRuleSchema, SystemSettingSchema
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

@router.get("/lead-rules", response_model=List[LeadDaysRuleSchema])
async def get_lead_days_rules(db: Session = Depends(get_db)):
    """
    Returns configured Lead Days pricing adjustment rules.
    """
    rules = db.query(LeadDaysRule).all()
    if not rules:
        # Seed default rules
        DEFAULT_LEAD_RULES = [
            {"min_days": 0, "max_days": 2, "adjustment_pct": 20.0, "description": "Last-minute booking adjustment (0-2 days)"},
            {"min_days": 3, "max_days": 7, "adjustment_pct": 10.0, "description": "Short-lead booking adjustment (3-7 days)"},
            {"min_days": 8, "max_days": 15, "adjustment_pct": 5.0, "description": "Standard booking adjustment (8-15 days)"},
            {"min_days": 16, "max_days": 30, "adjustment_pct": 0.0, "description": "Baseline booking window (16-30 days)"},
            {"min_days": 31, "max_days": 60, "adjustment_pct": -5.0, "description": "Early bird booking discount (31-60 days)"},
            {"min_days": 61, "max_days": 9999, "adjustment_pct": -10.0, "description": "Super early bird discount (60+ days)"}
        ]
        for s in DEFAULT_LEAD_RULES:
            r = LeadDaysRule(
                min_days=s["min_days"],
                max_days=s["max_days"],
                adjustment_pct=s["adjustment_pct"],
                description=s["description"]
            )
            db.add(r)
        db.commit()
        rules = db.query(LeadDaysRule).all()

    return [
        {
            "id": r.id,
            "min_days": r.min_days,
            "max_days": r.max_days,
            "adjustment_pct": r.adjustment_pct,
            "description": r.description,
            "is_active": r.is_active
        } for r in rules
    ]

@router.post("/lead-rules")
async def update_lead_days_rules(rules: List[LeadDaysRuleSchema], db: Session = Depends(get_db)):
    """
    Saves/updates Lead Days pricing adjustment rules.
    """
    try:
        db.query(LeadDaysRule).delete()
        for r in rules:
            rule = LeadDaysRule(
                min_days=r.min_days,
                max_days=r.max_days,
                adjustment_pct=r.adjustment_pct,
                description=r.description,
                is_active=r.is_active
            )
            db.add(rule)
        db.commit()
        return {"status": "success", "message": "Lead Days rules updated successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update Lead Days rules: {str(e)}")

@router.get("/settings", response_model=List[SystemSettingSchema])
async def get_system_settings(db: Session = Depends(get_db)):
    """
    Returns global system settings. Seeds defaults if empty.
    """
    settings = db.query(SystemSetting).all()
    if not settings:
        # Seed default settings
        DEFAULT_SETTINGS = [
            {"key": "guest_surcharge_per_person", "value": "300.0", "description": "Surcharge amount in ₹ per extra person exceeding baseline capacity."},
            {"key": "guest_surcharge_threshold", "value": "15", "description": "Baseline guest count capacity. Surcharges apply to guest counts above this."},
            {"key": "ENABLE_EXPECTED_REVENUE_OPTIMIZATION", "value": "false", "description": "Toggles Phase 4 expected revenue optimization simulation on price predictions."}
        ]

        for s in DEFAULT_SETTINGS:
            setting = SystemSetting(
                key=s["key"],
                value=s["value"],
                description=s["description"]
            )
            db.add(setting)
        db.commit()
        settings = db.query(SystemSetting).all()
    
    return [
        {
            "key": s.key,
            "value": s.value,
            "description": s.description
        } for s in settings
    ]

@router.post("/settings")
async def update_system_settings(settings: List[SystemSettingSchema], db: Session = Depends(get_db)):
    """
    Updates global system settings.
    """
    try:
        for s in settings:
            db_setting = db.query(SystemSetting).filter(SystemSetting.key == s.key).first()
            if db_setting:
                db_setting.value = s.value
                db_setting.description = s.description
            else:
                new_setting = SystemSetting(
                    key=s.key,
                    value=s.value,
                    description=s.description
                )
                db.add(new_setting)
        db.commit()
        return {"status": "success", "message": "System settings updated successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update system settings: {str(e)}")
