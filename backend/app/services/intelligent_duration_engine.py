import pandas as pd
from typing import Dict, Any

class IntelligentDurationEngine:
    """
    Intelligent Duration Engine
    Handles normalizing historical prices based on duration discrepancies (Short Stay Discounts).
    Uses a 50% Fixed / 50% Variable heuristic for normalization.
    """
    
    @classmethod
    def get_standard_duration(cls, commercial_slot: str) -> float:
        """Returns the standard expected duration for a given commercial slot."""
        slot = str(commercial_slot).upper()
        if "12H" in slot or "DAY" in slot and "24H" not in slot and "EXTENDED" not in slot:
            if "COUPLE" in slot:
                return 5.0 # Couple Half Day is typically around 5-6 hours
            return 12.0
        elif "24H" in slot:
            return 24.0
        elif "COUPLE HALF DAY" in slot:
            return 5.0
        elif "EXTENDED" in slot:
            # We don't normalize extended stay here, as it's handled by its own engine.
            return 24.0
        return 24.0

    @classmethod
    def normalize_price_for_training(cls, selling_price: float, duration_hours: float, commercial_slot: str) -> float:
        """
        Normalizes a short-stay distress price to its full standard slot equivalent.
        E.g., if standard is 12H, and user booked 5H for 500, we convert that 500 to the 12H equivalent.
        Uses 50% fixed, 50% variable cost logic.
        """
        if pd.isna(selling_price) or pd.isna(duration_hours) or selling_price <= 0:
            return selling_price
            
        std_dur = cls.get_standard_duration(commercial_slot)
        
        # Don't penalize or inflate if duration is basically the standard or greater
        # E.g. booking 11 hours in a 12 hour slot is normal.
        if duration_hours >= std_dur - 1.0:
            return selling_price
            
        # Avoid division by zero
        if duration_hours <= 0:
            return selling_price
            
        # Removed: Hardcoded 50% fixed/variable heuristic. 
        # The ML model will natively learn short-stay discounts via duration_ratio.
        return selling_price

    @classmethod
    def calculate_duration_adjustment(cls, context: Any) -> Dict[str, Any]:
        """
        Calculates a discount if the requested duration is significantly less than the standard slot duration.
        """
        req_dur = None
        if hasattr(context, 'request'):
            req_dur = context.request.get('duration_hours')
                
        if req_dur is None:
             return {"adjustment_amount": 0.0, "reason": "Duration not specified."}
             
        std_dur = cls.get_standard_duration(context.request.get('commercial_slot', '12H Day'))
        
        # Removed: Hardcoded duration discount heuristic.
        # Duration impact is now handled purely by ML prediction using duration_ratio.
        return {
            "discount_amount": 0.0,
            "explanation": "Duration effect learned strictly by ML model",
            "effective_duration_ratio": std_dur > 0 and (req_dur / std_dur) or 1.0,
            "std_duration": std_dur
        }
