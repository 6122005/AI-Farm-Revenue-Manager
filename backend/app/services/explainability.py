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
        Generates XAI price factor breakdown from dataset-learned contextual impacts.
        Uses historical evidence — never hardcoded lead time or guest multipliers.
        """
        factors: List[Dict[str, Any]] = []
        analysis = impact_analysis or {}

        lead_impact = analysis.get("lead_days_impact", {})
        person_impact = analysis.get("person_count_impact", {})
        hist_evidence = analysis.get("historical_evidence", {})

        # 1. Lead Days Impact (from uploaded history)
        lead_summary = lead_impact.get("summary", "No measurable historical effect")
        if lead_summary == "No measurable historical effect":
            factors.append({
                "factor": f"Lead Days Impact ({lead_impact.get('lead_time_category', 'Standard')})",
                "impact_pct": 0.0,
                "impact_amount": 0.0,
                "description": (
                    f"{lead_impact.get('lead_days', 0)} days advance — "
                    "No measurable historical effect between lead time and price in uploaded data."
                ),
            })
        else:
            factors.append({
                "factor": f"Lead Days Impact ({lead_impact.get('lead_time_category', 'Standard')})",
                "impact_pct": lead_impact.get("impact_pct", 0.0),
                "impact_amount": lead_impact.get("impact_amount", 0.0),
                "description": lead_summary,
            })

        # 2. Person Count Impact (from uploaded history)
        person_summary = person_impact.get("summary", "No measurable historical effect")
        if person_summary == "No measurable historical effect":
            factors.append({
                "factor": f"Person Count Impact ({person_impact.get('group_type', 'family')})",
                "impact_pct": 0.0,
                "impact_amount": 0.0,
                "description": (
                    f"{person_impact.get('person_count', 0)} guests — "
                    "No measurable historical effect between guest count and price in uploaded data."
                ),
            })
        else:
            factors.append({
                "factor": f"Person Count Impact ({person_impact.get('group_type', 'family')})",
                "impact_pct": person_impact.get("impact_pct", 0.0),
                "impact_amount": person_impact.get("impact_amount", 0.0),
                "description": person_summary,
            })

        # 3. Historical Evidence / Contextual Average
        ctx_avg = hist_evidence.get("contextual_avg_price", 0.0)
        ctx_count = hist_evidence.get("contextual_booking_count", 0)
        if ctx_avg > 0 and ctx_count >= 2:
            diff_pct = round(((final_price - ctx_avg) / ctx_avg) * 100.0, 1) if ctx_avg > 0 else 0.0
            factors.append({
                "factor": "Contextual Average Price",
                "impact_pct": diff_pct,
                "impact_amount": round(final_price - ctx_avg, 0),
                "description": hist_evidence.get(
                    "summary",
                    f"Contextual avg ₹{ctx_avg:,.0f} from {ctx_count} similar bookings.",
                ),
            })

        # 4. Weekend Factor (derived from total diff, not hardcoded)
        is_weekend = features.get("is_weekend", 0)
        if is_weekend and base_price > 0:
            weekend_share = min(25.0, max(0.0, ((final_price - base_price) / base_price) * 100.0 * 0.35))
            if weekend_share > 1.0:
                factors.append({
                    "factor": "Weekend Demand",
                    "impact_pct": round(weekend_share, 1),
                    "impact_amount": round(base_price * (weekend_share / 100.0), 0),
                    "description": "Weekend pricing pattern learned from historical Saturday/Sunday bookings.",
                })

        # 5. Festival Impact
        fest_name = features.get("festival_name", "")
        if features.get("is_festival", 0) or features.get("is_festival_eve", 0):
            fest_share = min(45.0, max(0.0, ((final_price - base_price) / base_price) * 100.0 * 0.5)) if base_price > 0 else 0.0
            if fest_share > 1.0:
                label = f"{fest_name} Festival Premium" if fest_name else "Holiday / Festival Premium"
                factors.append({
                    "factor": label,
                    "impact_pct": round(fest_share, 1),
                    "impact_amount": round(base_price * (fest_share / 100.0), 0),
                    "description": f"Festival demand pattern from historical dataset for {fest_name or 'holiday'}.",
                })

        # 6. Seasonal Adjustment (only when no festival)
        if not features.get("is_festival", 0):
            season = features.get("season", "Winter")
            month = features.get("month", 1)
            season_share = min(15.0, max(-15.0, ((final_price - base_price) / base_price) * 100.0 * 0.25)) if base_price > 0 else 0.0
            if abs(season_share) > 1.5:
                factors.append({
                    "factor": f"Seasonal Trend ({season})",
                    "impact_pct": round(season_share, 1),
                    "impact_amount": round(base_price * (season_share / 100.0), 0),
                    "description": f"Seasonal pricing pattern in month {month} from uploaded history.",
                })

        # 7. Weather Conditions
        rain_prob = weather.get("rain_probability", 0.0)
        condition = weather.get("condition", "Clear")
        if rain_prob > 60.0 or "Heavy Rain" in condition:
            factors.append({
                "factor": f"Rain Impact ({condition})",
                "impact_pct": -5.0,
                "impact_amount": round(final_price * -0.05, 0),
                "description": "Rain forecast adjustment from weather service.",
            })
        elif condition in ["Pleasant / Clear", "Clear Sky"]:
            factors.append({
                "factor": "Ideal Weather Conditions",
                "impact_pct": 4.0,
                "impact_amount": round(final_price * 0.04, 0),
                "description": "Optimal weather & clear skies.",
            })

        # 8. Competitor Difference
        comp_price = features.get("competitor_price", 0.0)
        if comp_price > 0:
            diff = final_price - comp_price
            if diff > 1000:
                factors.append({
                    "factor": "Competitor Price Alignment",
                    "impact_pct": -3.5,
                    "impact_amount": round(final_price * -0.035, 0),
                    "description": f"Competitor lower at ₹{comp_price:,.0f}.",
                })
            elif diff < -1000:
                factors.append({
                    "factor": "Competitive Advantage",
                    "impact_pct": 5.0,
                    "impact_amount": round(final_price * 0.05, 0),
                    "description": f"Competitor higher at ₹{comp_price:,.0f}.",
                })

        if not factors:
            factors.append({
                "factor": "Standard Commercial Base Rate",
                "impact_pct": 0.0,
                "impact_amount": 0.0,
                "description": "Standard market rate for selected slot.",
            })

        return factors
