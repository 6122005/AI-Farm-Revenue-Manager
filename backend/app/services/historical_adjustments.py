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
        Rule 6: Festival Engine V2
        Uses Sheet4 (via festival_engine) history, borrows progressively if no history exists.
        """
        req_date = context.request.get("start_datetime")
        df = context.retrieved_segment
        base_price = context.base_price
        
        try:
            dt_in = datetime.strptime(req_date, "%Y-%m-%d %H:%M")
            dt_out = dt_in + timedelta(hours=12) # Approximation to check overlap
        except:
            return {"adjustment_amount": 0.0, "reason": "Invalid date format for festival check."}
            
        overlap_info = festival_engine.detect_festivals(dt_in, dt_out)
        is_festival = overlap_info.get("is_festival", False)
        festival_name = overlap_info.get("festival_name", "Festival")
        
        if not is_festival:
            return {
                "adjustment_amount": 0.0,
                "reason": "No festival detected on this date."
            }
            
        df_fest = df[df['is_festival'] == 1] if 'is_festival' in df.columns else pd.DataFrame()
        
        if not df_fest.empty:
            fest_median = context.get_segment_median(df_fest)
            adj = fest_median - base_price
            return {
                "adjustment_amount": float(adj),
                "reason": f"{festival_name}: Historical festival median in this segment is ₹{fest_median:.0f}. Adj: ₹{adj:.0f}."
            }
            
        insights = FeatureEngineer._load_insights()
        learned_intel = FeatureEngineer._load_festival_intelligence()
        if festival_name in learned_intel:
            mult = learned_intel[festival_name]
            reason = f"{festival_name}: Borrowed learned specific multiplier ({mult:.2f}x)."
        else:
            mult = insights.get("festival_premium_ratio", 1.30)
            reason = f"{festival_name}: Borrowed global historical festival multiplier ({mult:.2f}x)."
            
        adj = (base_price * mult) - base_price
        return {
            "adjustment_amount": float(adj),
            "reason": reason
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
