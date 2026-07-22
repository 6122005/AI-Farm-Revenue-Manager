import pandas as pd
from typing import Dict, Any, List, Optional


class ExplainableAI:
    @staticmethod
    def generate_price_factors(
        base_price: float,
        final_price: float,
        features: Dict[str, Any],
        weather: Dict[str, Any],
        impact_analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Phase 8 & 9: Explainable AI Price Factors and Deconstruction.
        Deconstructs final price dynamically into component adjustments.
        """
        factors: List[Dict[str, Any]] = []
        
        # 1. Base Market Price
        factors.append({
            "factor": "Base Market Price",
            "impact_pct": 0.0,
            "impact_amount": float(round(base_price, -2)),
            "description": "Standard median baseline price for this slot category learned from historical dataset."
        })

        # 2. Weekend Premium
        is_weekend = features.get("is_weekend", 0)
        weekend_ratio = features.get("weekend_premium_ratio", 1.25)
        if is_weekend:
            val = float(round(base_price * (weekend_ratio - 1.0), -2))
            pct = round((weekend_ratio - 1.0) * 100.0, 1)
            factors.append({
                "factor": "Weekend Premium",
                "impact_pct": pct,
                "impact_amount": val,
                "description": f"Weekend demand multiplier (+{pct}%) learned from Saturday/Sunday booking patterns."
            })

        # 3. Lead Time Adjustment
        lead_days = features.get("lead_days", 7)
        lead_ratio = features.get("advance_booking_ratio", 1.10)
        if lead_days > 14:
            val = float(round(base_price * (lead_ratio - 1.0), -2))
            pct = round((lead_ratio - 1.0) * 100.0, 1)
            factors.append({
                "factor": "Lead Time Adjustment (Advance)",
                "impact_pct": pct,
                "impact_amount": val,
                "description": f"Advance booking premium of +{pct}% for reserving {lead_days} days in advance."
            })
        elif lead_days < 2:
            val = float(round(base_price * -0.10, -2))
            factors.append({
                "factor": "Lead Time Adjustment (Last Minute)",
                "impact_pct": -10.0,
                "impact_amount": val,
                "description": f"Discount of -10% applied for last-minute booking ({lead_days} days lead)."
            })

        # 4. Guest Count / Couple Adjustment
        person_count = features.get("person_count", 4)
        if features.get("is_couple", 0):
            val = float(round(base_price * -0.15, -2))
            factors.append({
                "factor": "Guest Count Adjustment (Couple)",
                "impact_pct": -15.0,
                "impact_amount": val,
                "description": "Discount of -15% for Couple Slot occupancy (reduced resource & utility usage)."
            })
        elif features.get("is_corporate", 0):
            val = float(round(base_price * 0.20, -2))
            factors.append({
                "factor": "Guest Count Adjustment (Corporate/Large Group)",
                "impact_pct": 20.0,
                "impact_amount": val,
                "description": f"Premium of +20% for large group occupancy of {person_count} guests."
            })

        # 5. Demand Regime & Seasonal Adjustment
        season = features.get("season", "Winter")
        summer_ratio = features.get("summer_demand_ratio", 1.20)
        
        if features.get("is_peak_season", 0):
            pct = round((summer_ratio - 1.0) * 100.0, 1) if season == "Summer" else 10.0
            val = float(round(base_price * (pct / 100.0), -2))
            factors.append({
                "factor": f"Demand Regime Adjustment (Peak {season})",
                "impact_pct": pct,
                "impact_amount": val,
                "description": f"Seasonal high-demand adjustment of +{pct}% during peak booking period."
            })
        elif features.get("is_off_season", 0):
            factors.append({
                "factor": f"Demand Regime Adjustment (Off-Peak {season})",
                "impact_pct": -12.0,
                "impact_amount": float(round(base_price * -0.12, -2)),
                "description": f"Off-peak demand discount of -12.0% based on historical monthly low booking activity."
            })

        # 6. Weather Adjustment
        rain_prob = weather.get("rain_probability", 0.0)
        condition = weather.get("condition", "Clear Sky")
        temp = weather.get("temperature", 26.0)
        rain_ratio = features.get("rain_impact_ratio", 0.85)
        
        if rain_prob > 50.0:
            pct = round((rain_ratio - 1.0) * 100.0, 1)
            val = float(round(base_price * (pct / 100.0), -2))
            factors.append({
                "factor": f"Weather Adjustment (Rain Impact: {condition})",
                "impact_pct": pct,
                "impact_amount": val,
                "description": f"Weather risk reduction of {pct}% based on forecasted {rain_prob}% rain probability."
            })
        elif condition in ["Pleasant / Clear", "Sunny / Warm"] or (22.0 <= temp <= 28.0):
            factors.append({
                "factor": "Weather Adjustment (Pleasant Conditions)",
                "impact_pct": 5.0,
                "impact_amount": float(round(base_price * 0.05, -2)),
                "description": f"Weather premium of +5.0% for pleasant temperature ({temp}°C) and clear skies."
            })

        # 7. Festival / Holiday Adjustment
        if features.get("is_festival", 0) or features.get("is_festival_eve", 0):
            fest_name = features.get("festival_name", "Holiday")
            factors.append({
                "factor": f"Festival Premium ({fest_name})",
                "impact_pct": 25.0,
                "impact_amount": float(round(base_price * 0.25, -2)),
                "description": f"Festival markup (+25.0%) for booking date falling on or near holiday: {fest_name}."
            })

        return factors
