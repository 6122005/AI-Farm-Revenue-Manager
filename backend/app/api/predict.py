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
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

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
