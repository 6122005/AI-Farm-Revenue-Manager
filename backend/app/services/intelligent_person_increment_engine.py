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
        
        # 3. Calculate strictly additive extra guests
        extra_guests = max(0.0, float(req_guests - anchor_guests))
        
        # 4. Apply flat rate
        adj = float(extra_guests * slope)
        
        return {
            "adjustment_amount": adj,
            "reason": f"Standard capacity is {anchor_guests:.1f} guests. Added flat ₹{slope} for {extra_guests:.1f} extra guests.",
            "evidence": {
                "slope": float(slope),
                "anchor_guests": float(anchor_guests),
                "extra_guests": float(extra_guests)
            }
        }
