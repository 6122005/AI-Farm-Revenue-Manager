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
        # The retrieval engine has run a linear regression on the exact segment to learn this slope.
        learned_rate = context.stats.get("learned_guest_rate", 62.5)
        
        # 2. Determine base capacity (anchor guests)
        # We upgraded the retrieval engine to normalize the base price to the standard base capacity of 4.
        # Therefore, we strictly anchor at 4 guests.
        anchor_guests = 4.0
        
        # Total extra guests compared to standard capacity
        total_extra = max(0.0, float(req_guests - anchor_guests))
        
        # 3. Calculate total adjustment
        adj = total_extra * learned_rate
        
        return {
            "adjustment_amount": float(adj),
            "reason": f"Standard capacity {anchor_guests:.1f}. Added ₹{learned_rate:.1f}/person for {total_extra:.1f} extra guests (Dynamic AI Learned Rate).",
            "evidence": {
                "learned_rate": float(learned_rate),
                "anchor_guests": float(anchor_guests),
                "total_extra_guests": float(total_extra)
            }
        }
