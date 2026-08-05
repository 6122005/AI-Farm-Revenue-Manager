import pandas as pd
import numpy as np
from typing import Dict, Any
from app.services.pricing_context import PricingContext

class IntelligentPersonIncrementEngine:
    
    @classmethod
    def calculate_guest_increment(cls, context: PricingContext) -> Dict[str, Any]:
        """
        Rule 4: Person Increment Engine V2
        Uses exact nearest lower and upper historical data from the SAME segment pool.
        """
        req_guests = context.request.get("person_count", 4)
        df = context.retrieved_segment
        base_price = context.base_price
        
        if df.empty:
            return {
                "adjustment_amount": 0.0,
                "reason": "No historical evidence for guest variation. (Default +₹0)",
                "evidence": {}
            }
            
        # Group by person count to get medians for this specific segment
        guest_medians = df.groupby('person_count')['selling_price'].median().to_dict()
        
        if req_guests in guest_medians:
            diff = guest_medians[req_guests] - base_price
            return {
                "adjustment_amount": float(diff),
                "reason": f"Exact historical match for {req_guests} guests yields a segment difference of ₹{diff:.0f}.",
                "evidence": {"exact_match": True, "lower": req_guests, "upper": req_guests}
            }
            
        available_guests = sorted(list(guest_medians.keys()))
        lower_guests = [g for g in available_guests if g < req_guests]
        upper_guests = [g for g in available_guests if g > req_guests]
        
        nearest_lower = max(lower_guests) if lower_guests else None
        nearest_upper = min(upper_guests) if upper_guests else None
        
        # If we have both, interpolate
        if nearest_lower is not None and nearest_upper is not None:
            price_lower = guest_medians[nearest_lower]
            price_upper = guest_medians[nearest_upper]
            guest_diff = nearest_upper - nearest_lower
            price_diff = price_upper - price_lower
            
            if guest_diff == 0:
                per_person = 0.0
            else:
                per_person = max(0.0, price_diff / guest_diff)
                
            # We scale from the representative baseline, but to be safe and anchored:
            # The representative baseline is our starting point.
            # We should calculate the theoretical price for req_guests using the slope from the nearest lower.
            theoretical_price = price_lower + (per_person * (req_guests - nearest_lower))
            adj = theoretical_price - base_price
            
            return {
                "adjustment_amount": float(adj),
                "reason": f"Interpolated between {nearest_lower} and {nearest_upper} guests (Slope: ₹{per_person:.0f}/person). Total Adjustment: ₹{adj:.0f}.",
                "evidence": {"lower_guests": nearest_lower, "upper_guests": nearest_upper, "slope": per_person}
            }
            
        # If only lower exists, extrapolate upwards
        if nearest_lower is not None:
            # We need a slope. If there's another lower, use it. Otherwise, default to conservative 100/person.
            if len(lower_guests) > 1:
                second_lower = lower_guests[-2]
                g_diff = nearest_lower - second_lower
                p_diff = guest_medians[nearest_lower] - guest_medians[second_lower]
                per_person = max(0.0, p_diff / g_diff) if g_diff > 0 else 100.0
            else:
                # Safe fallback if we can't build a historical slope
                per_person = 150.0
                
            theoretical_price = guest_medians[nearest_lower] + (per_person * (req_guests - nearest_lower))
            adj = theoretical_price - base_price
            return {
                "adjustment_amount": float(adj),
                "reason": f"Extrapolated from {nearest_lower} guests upwards (Slope: ₹{per_person:.0f}/person). Total Adj: ₹{adj:.0f}.",
                "evidence": {"lower_guests": nearest_lower, "upper_guests": None, "slope": per_person}
            }
            
        # If only upper exists, extrapolate downwards
        if nearest_upper is not None:
            if len(upper_guests) > 1:
                second_upper = upper_guests[1]
                g_diff = second_upper - nearest_upper
                p_diff = guest_medians[second_upper] - guest_medians[nearest_upper]
                per_person = max(0.0, p_diff / g_diff) if g_diff > 0 else 100.0
            else:
                per_person = 150.0
                
            theoretical_price = guest_medians[nearest_upper] - (per_person * (nearest_upper - req_guests))
            adj = theoretical_price - base_price
            return {
                "adjustment_amount": float(adj),
                "reason": f"Extrapolated downwards from {nearest_upper} guests (Slope: ₹{per_person:.0f}/person). Total Adj: ₹{adj:.0f}.",
                "evidence": {"lower_guests": None, "upper_guests": nearest_upper, "slope": per_person}
            }
            
        return {
            "adjustment_amount": 0.0,
            "reason": "Unexpected guest calculation failure.",
            "evidence": {}
        }
