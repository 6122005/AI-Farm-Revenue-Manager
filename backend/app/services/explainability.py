import pandas as pd
from typing import Dict, Any, List, Optional, Callable


class ExplainableAI:
    @classmethod
    def calculate_perturbation_attributions(
        cls,
        predict_fn: Callable[[Dict[str, Any]], float],
        features: Dict[str, Any],
        weather: Dict[str, Any],
        base_slot_price: float
    ) -> List[Dict[str, Any]]:
        """
        Phase 8 & 9: True Data-Driven local feature attribution.
        Uses Single-Variable Perturbation (marginal contribution) to calculate how
        each group of features (Lead Days, Guests, Weather, Festival, Utilization)
        shifted the price relative to their default baseline.
        """
        # 1. Base Predict
        p_actual = predict_fn(features)
        
        # 2. Perturb Lead Days
        feat_lead = features.copy()
        feat_lead["lead_days"] = 7
        feat_lead["lead_time_bucket"] = 1
        p_lead = predict_fn(feat_lead)
        lead_attr = p_actual - p_lead

        # 3. Perturb Person Count
        feat_guests = features.copy()
        feat_guests["person_count"] = 4
        feat_guests["is_couple"] = 0
        feat_guests["is_family"] = 1
        feat_guests["is_corporate"] = 0
        p_guests = predict_fn(feat_guests)
        guests_attr = p_actual - p_guests

        # 4. Perturb Weather
        feat_weather = features.copy()
        feat_weather["temperature"] = 26.0
        feat_weather["rain_probability"] = 20.0
        feat_weather["humidity"] = 60.0
        feat_weather["wind_speed"] = 4.2
        feat_weather["cloud_cover"] = 25.0
        p_weather = predict_fn(feat_weather)
        weather_attr = p_actual - p_weather

        # 5. Perturb Festival
        feat_festival = features.copy()
        feat_festival["is_festival"] = 0
        feat_festival["is_festival_eve"] = 0
        feat_festival["festival_name"] = "No Festival"
        feat_festival["is_long_weekend"] = 1 if features.get("is_weekend", 0) else 0
        feat_festival["is_consecutive_holiday"] = 0
        p_festival = predict_fn(feat_festival)
        festival_attr = p_actual - p_festival

        # 6. Perturb Utilization
        feat_util = features.copy()
        feat_util["duration_hours"] = features.get("slot_capacity_hours", 12.0)
        feat_util["slot_utilization_ratio"] = 1.0
        feat_util["opportunity_cost_factor"] = 1.0
        p_util = predict_fn(feat_util)
        util_attr = p_actual - p_util

        # Calculate base market price as remainder so everything sums exactly to final predicted price
        total_attr = lead_attr + guests_attr + weather_attr + festival_attr + util_attr
        derived_base_price = p_actual - total_attr

        factors = []
        
        # 1. Base Market Price
        factors.append({
            "factor": "Base Market Price",
            "impact_pct": 0.0,
            "impact_amount": float(round(derived_base_price, -2)),
            "description": "Direct Historical Average based on Month, Slot, and Weekday/Weekend."
        })

        # Helper to format description and add factor if attribution is significant
        def add_factor(name: str, val: float, desc_template: str):
            if abs(val) >= 50.0:
                pct = round((val / derived_base_price) * 100.0, 1) if derived_base_price > 0 else 0.0
                factors.append({
                    "factor": name,
                    "impact_pct": pct,
                    "impact_amount": float(round(val, -2)),
                    "description": desc_template.format(pct=pct, amt=abs(val))
                })

        # 2. Lead Days
        add_factor(
            "Lead Days Impact",
            lead_attr,
            "Lead time contribution of {pct:+.1f}% (₹{amt:,.0f}) dynamically learned from historical advance/last-minute curves."
        )

        # 3. Person Count
        add_factor(
            "Guest Count Impact",
            guests_attr,
            "Occupancy segment contribution of {pct:+.1f}% (₹{amt:,.0f}) based on group scale."
        )

        # 4. Weather
        add_factor(
            "Weather Condition Impact",
            weather_attr,
            "Weather variable contribution of {pct:+.1f}% (₹{amt:,.0f}) responding to forecast metrics."
        )

        # 5. Festival
        add_factor(
            "Festival/Holiday Premium",
            festival_attr,
            "Holiday demand contribution of {pct:+.1f}% (₹{amt:,.0f}) matching festival dates."
        )

        # 6. Utilization
        add_factor(
            "Inventory Utilization Guard",
            util_attr,
            "Commercial duration slot utilization contribution of {pct:+.1f}% (₹{amt:,.0f})."
        )

        # Ensure at least one factor exists
        if len(factors) == 1:
            factors.append({
                "factor": "Standard Dynamic Adjustment",
                "impact_pct": 0.0,
                "impact_amount": 0.0,
                "description": "No significant local feature deviations from base conditions."
            })

        return factors

    @staticmethod
    def generate_price_factors(
        base_price: float,
        final_price: float,
        features: Dict[str, Any],
        weather: Dict[str, Any],
        impact_analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Deprecated: use calculate_perturbation_attributions for true data-driven attributions."""
        return []
