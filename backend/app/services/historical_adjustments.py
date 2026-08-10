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
        req_lead = context.request.get("lead_days", 0)
        # Fetch AI-learned dynamic lead slope and mean lead days from historical stats
        learned_slope = context.stats.get("learned_lead_slope", 0.0)
        mean_lead_days = context.stats.get("mean_lead_days", 7.0)
        
        # Calculate difference from standard booking window
        diff_days = float(req_lead) - mean_lead_days
        
        # Total adjustment based on AI learned slope
        adj = diff_days * learned_slope
        
        if adj > 0:
            word = "premium"
            sign = "+"
        else:
            word = "discount"
            sign = ""
            
        reason = f"{req_lead} days lead time (Avg is {mean_lead_days:.1f}). Applying AI Learned Slope of ₹{learned_slope:.1f}/day. {sign}₹{adj:.0f} {word}."
            
        return {
            "adjustment_amount": float(adj),
            "reason": reason
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
        base_price = context.base_price
        
        if count >= 15:
            adj = base_price * 0.05
            return {"adjustment_amount": float(adj), "reason": f"High demand detected ({count} similar historical bookings). (+5%)"}
        elif count <= 2:
            adj = -base_price * 0.05
            return {"adjustment_amount": float(adj), "reason": f"Low demand detected ({count} similar historical bookings). (-5%)"}
            
        return {"adjustment_amount": 0.0, "reason": "Normal historical demand pattern. (+₹0)"}
        
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
            adj = -base_price * 0.10
            return {"adjustment_amount": float(adj), "reason": f"Heavy Rain / Bad Weather forecasted. Applying 10% discount (-₹{abs(adj):.0f})."}
        elif "rain" in condition or rain_prob > 40:
            adj = -base_price * 0.05
            return {"adjustment_amount": float(adj), "reason": f"Rain forecasted. Applying 5% discount (-₹{abs(adj):.0f})."}
        elif ("clear" in condition or "sunny" in condition) and context.request.get("is_weekend", False):
            adj = base_price * 0.03
            return {"adjustment_amount": float(adj), "reason": f"Clear/Sunny weekend weather. Applying 3% premium (+₹{adj:.0f})."}
            
        return {"adjustment_amount": 0.0, "reason": f"Weather forecast is {condition.title()} (No Adjustment)."}
