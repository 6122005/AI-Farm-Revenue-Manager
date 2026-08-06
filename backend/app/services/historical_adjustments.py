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
        df = context.retrieved_segment
        base_price = context.base_price
        
        # User-defined explicit business rules for lead days
        if req_lead <= 14:
            adj = 0.0
            reason = f"Lead time is {req_lead} days. Within standard short-term window (+₹0)."
        elif req_lead <= 30:
            adj = 200.0
            reason = f"Lead time is {req_lead} days (15-30 day window). Applying advance booking premium (+₹200)."
        else:
            adj = 300.0
            reason = f"Lead time is {req_lead} days (31+ day window). Applying long-advance booking premium (+₹300)."
            
        return {
            "adjustment_amount": adj,
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
        return {"adjustment_amount": 0.0, "reason": "Weather forecast is Clear (No Adjustment)."}
