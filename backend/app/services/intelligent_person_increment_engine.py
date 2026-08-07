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
            
        # 1. Use user-approved flat rate per person (₹62.5/person = ₹500 for 8 extra people)
        slope = 62.5
        
        # 2. Determine base capacity (anchor guests)
        # If the segment has data, we find the average guest count for those bookings.
        # Otherwise, assume 2 guests (couple).
        anchor_guests = df['person_count'].mean() if not df.empty else 2.0
        
        # 3. Calculate tiered extra guests
        # Tier 1: Guests between anchor_guests and 15 (₹62.5 per person)
        # Tier 2: Guests above 15 (₹100 per person)
        
        tier1_rate = 62.5
        tier2_rate = 100.0
        tier2_threshold = 15.0
        
        # Total extra guests compared to standard capacity
        total_extra = max(0.0, float(req_guests - anchor_guests))
        
        tier1_guests = 0.0
        tier2_guests = 0.0
        
        if req_guests > anchor_guests:
            if req_guests <= tier2_threshold:
                # All extra guests fall in Tier 1
                tier1_guests = float(req_guests - anchor_guests)
            else:
                # Some or all extra guests fall in Tier 2
                if anchor_guests >= tier2_threshold:
                    # Anchor is already >= 15, so all extra are Tier 2
                    tier2_guests = float(req_guests - anchor_guests)
                else:
                    # Anchor is < 15, req is > 15. Mix of Tier 1 and Tier 2
                    tier1_guests = float(tier2_threshold - anchor_guests)
                    tier2_guests = float(req_guests - tier2_threshold)
                    
        # 4. Calculate total adjustment
        tier1_adj = tier1_guests * tier1_rate
        tier2_adj = tier2_guests * tier2_rate
        adj = tier1_adj + tier2_adj
        
        return {
            "adjustment_amount": float(adj),
            "reason": f"Standard capacity {anchor_guests:.1f}. Added ₹{tier1_rate} for {tier1_guests:.1f} guests up to 15, and ₹{tier2_rate} for {tier2_guests:.1f} guests beyond 15.",
            "evidence": {
                "tier1_rate": float(tier1_rate),
                "tier2_rate": float(tier2_rate),
                "tier1_guests": float(tier1_guests),
                "tier2_guests": float(tier2_guests),
                "anchor_guests": float(anchor_guests),
                "total_extra_guests": float(total_extra)
            }
        }
