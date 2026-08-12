import pandas as pd
import numpy as np
from typing import Dict, Any
from app.services.pricing_context import PricingContext

class IntelligentPersonIncrementEngine:
    
    @classmethod
    def calculate_guest_increment(cls, context: PricingContext) -> Dict[str, Any]:
        """
        Enterprise Person Increment Engine
        Features: Adaptive Neighbor Search, Additive-Only Scaling
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
            
        # 1. Fetch AI-learned dynamic guest rate from historical stats
        # Ensure monotonic property (more guests >= price).
        raw_rate = float(context.stats.get("learned_guest_rate", 62.5))
        learned_rate = max(0.0, raw_rate)
        
        # 2. Determine base capacity (anchor guests)
        # Retrieval engine normalizes base price to standard capacity of 4.
        anchor_guests = 4.0
        
        # Calculate diff from standard capacity (can be negative for discounts)
        diff_guests = float(req_guests - anchor_guests)
        
        # 3. Distance-based Shrinkage (Extrapolation Penalty)
        hist_guests = df["person_count"].dropna().values if "person_count" in df.columns else np.array([])
        if len(hist_guests) > 0:
            hist_min = float(np.min(hist_guests))
            hist_max = float(np.max(hist_guests))
        else:
            hist_min, hist_max = anchor_guests, anchor_guests
            
        extrap_dist = 0.0
        if req_guests < hist_min:
            extrap_dist = hist_min - req_guests
        elif req_guests > hist_max:
            extrap_dist = req_guests - hist_max
            
        # Shrink the adjustment strength by 10% for every guest outside the observed historical range (max 80% shrinkage)
        shrink_factor = max(0.2, 1.0 - (extrap_dist * 0.10))
        effective_rate = learned_rate * shrink_factor
        
        # 4. Calculate total adjustment
        adj = diff_guests * effective_rate
        
        sign = "+" if adj >= 0 else ""
        extrap_msg = f" (Extrapolation shrunk by {100-(shrink_factor*100):.0f}%)" if shrink_factor < 1.0 else ""
        
        return {
            "adjustment_amount": float(adj),
            "reason": f"Base 4 guests. {sign}₹{effective_rate:.1f}/person for {diff_guests:+.1f} guests from standard.{extrap_msg}",
            "evidence": {
                "raw_learned_rate": float(raw_rate),
                "effective_rate": float(effective_rate),
                "extrap_dist": float(extrap_dist),
                "shrink_factor": float(shrink_factor),
                "diff_guests": float(diff_guests)
            }
        }
