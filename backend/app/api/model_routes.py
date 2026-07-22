from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import pandas as pd

from app.models.schemas import RollbackRequest
from app.services.ml_trainer import MLTrainer
from app.services.drift_detector import drift_detector
from app.services.data_pipeline import CLEAN_DATA_PATH

router = APIRouter(prefix="/api/models", tags=["Model Management & Version Registry"])

@router.get("/versions")
async def get_model_versions():
    """
    Returns list of all trained model versions with TimeSeriesSplit validation metrics and promotion status.
    """
    try:
        history = MLTrainer.get_version_history()
        return {
            "status": "success",
            "total_versions": len(history),
            "versions": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch model versions: {str(e)}")

@router.post("/rollback")
async def rollback_model_version(request: RollbackRequest):
    """
    Rolls back the deployed champion model to a specific historical version ID.
    """
    try:
        res = MLTrainer.rollback_to_version(request.version_id)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")

@router.get("/drift-report")
async def get_data_drift_report():
    """
    Evaluates dataset drift between reference clean booking data and current distribution.
    """
    if not CLEAN_DATA_PATH.exists():
        return {
            "status": "no_data",
            "message": "No historical clean dataset found."
        }

    try:
        df = pd.read_csv(CLEAN_DATA_PATH)
        report = drift_detector.detect_drift(df, df)
        return {
            "status": "success",
            "drift_report": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {str(e)}")
