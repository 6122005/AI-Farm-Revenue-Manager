import pandas as pd
import numpy as np
from typing import Dict, Any
from app.services.pricing_context import PricingContext
from app.services.festival_engine import festival_engine
from app.services.feature_engineering import FeatureEngineer
from datetime import datetime, timedelta

class HistoricalAdjustments:
    
    @classmethod
    def calculate_lead_days_adjustment(cls, context: PricingContext) -> Dict[str, Any]:
        """
        Rule 5: Lead Days Engine V2
        Learn purely from historical data in the PricingContext. No fixed percentages.
        """
        req_lead = float(context.request.get("lead_days", 0))
        # Fetch AI-learned dynamic lead slope and mean lead days from historical stats
        learned_slope = float(context.stats.get("learned_lead_slope", 0.0))
        mean_lead_days = float(context.stats.get("mean_lead_days", 7.0))
        
        # Calculate difference from standard booking window
        diff_days = float(req_lead) - mean_lead_days
        
        # Distance-based Shrinkage (Extrapolation Penalty)
        df = context.retrieved_segment
        hist_leads = df["lead_days"].dropna().values if not df.empty and "lead_days" in df.columns else np.array([])
        if len(hist_leads) > 0:
            hist_min = float(np.min(hist_leads))
            hist_max = float(np.max(hist_leads))
        else:
            hist_min, hist_max = mean_lead_days, mean_lead_days
            
        extrap_dist = 0.0
        if req_lead < hist_min:
            extrap_dist = hist_min - req_lead
        elif req_lead > hist_max:
            extrap_dist = req_lead - hist_max
            
        # Shrink the adjustment strength by 10% for every day outside the observed historical range (max 80% shrinkage)
        shrink_factor = max(0.2, 1.0 - (extrap_dist * 0.10))
        effective_slope = learned_slope * shrink_factor
        
        # Total adjustment based on AI learned slope
        # Disabled manual lead adjustment to prevent double-counting (ML handles lead time)
        adj = 0.0
        
        if adj > 0:
            word = "premium"
            sign = "+"
        else:
            word = "discount"
            sign = ""
            
        extrap_msg = f" (Extrapolation shrunk by {100-(shrink_factor*100):.0f}%)" if shrink_factor < 1.0 else ""
        reason = f"{req_lead} days lead time. Native ML Baseline active. (Lead time absorbed by model)."
            
        return {
            "adjustment_amount": float(adj),
            "reason": reason,
            "evidence": {
                "raw_learned_slope": float(learned_slope),
                "effective_slope": float(effective_slope),
                "extrap_dist": float(extrap_dist),
                "shrink_factor": float(shrink_factor),
                "diff_days": float(diff_days)
            }
        }

    @classmethod
    def calculate_festival_premium(cls, context: PricingContext) -> Dict[str, Any]:
        """
        Rule 6: Festival Engine V2 (DISABLED)
        Disabled per user request.
        """
        return {
            "adjustment_amount": 0.0,
            "reason": "No Festival"
        }

    @classmethod
    def calculate_demand_adjustment(cls, context: PricingContext) -> Dict[str, Any]:
        count = context.booking_count
        
        # Disabled manual demand adjustment to prevent double-counting (ML handles volume)
        return {"adjustment_amount": 0.0, "reason": "Native ML Baseline active. (Demand absorbed by model)."}
        
    @classmethod
    def calculate_weather_adjustment(cls, context: PricingContext) -> Dict[str, Any]:
        from app.services.weather_service import weather_service
        
        booking_date = context.request.get("start_datetime", "").split(" ")[0]
        if not booking_date:
            return {"adjustment_amount": 0.0, "reason": "No booking date provided for weather."}
            
        forecast = weather_service.get_forecast(booking_date)
        condition = forecast.get("condition", "Clear").lower()
        rain_prob = forecast.get("rain_probability", 0.0)
        
        base_price = context.base_price
        
        if "heavy rain" in condition or "thunderstorm" in condition or rain_prob > 80:
            adj = 0.0
            return {"adjustment_amount": float(adj), "reason": f"Heavy Rain forecasted. (Discount already factored by ML engine)."}
        elif "rain" in condition or rain_prob > 40:
            adj = 0.0
            return {"adjustment_amount": float(adj), "reason": f"Rain forecasted. (Discount already factored by ML engine)."}
        elif ("clear" in condition or "sunny" in condition) and context.request.get("is_weekend", False):
            adj = 0.0
            return {"adjustment_amount": float(adj), "reason": f"Clear/Sunny weekend weather."}
            
        return {"adjustment_amount": 0.0, "reason": f"Weather forecast is {condition.title()} (No Adjustment)."}
