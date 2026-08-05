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
            
        # 1. Calculate global segment slope (per person cost)
        x = df['person_count'].values
        y = df['selling_price'].values
        if len(df) >= 3 and len(np.unique(x)) > 1:
            try:
                slope, _ = np.polyfit(x, y, 1)
                slope = max(0.0, slope) # strictly non-negative
            except:
                slope = 150.0
        else:
            slope = 150.0
            
        # 2. Adaptive Neighbor Search
        radius = 0
        max_radius = 5
        target_records = pd.DataFrame()
        
        while radius <= max_radius:
            lower_bound = req_guests - radius
            upper_bound = req_guests + radius
            target_records = df[(df['person_count'] >= lower_bound) & (df['person_count'] <= upper_bound)]
            if len(target_records) >= 8:
                break
            radius += 1
            
        if target_records.empty:
            target_records = df
            
        anchor_guests = target_records['person_count'].mean()
        anchor_price = target_records['selling_price'].median()
        
        # 3. Calculate Theoretical Price for exactly req_guests
        theoretical_price = anchor_price + slope * (req_guests - anchor_guests)
        
        # 4. Strict Additive Rule (Never subtract from Base Price)
        raw_adj = theoretical_price - base_price
        adj = float(max(0.0, raw_adj))
        
        return {
            "adjustment_amount": adj,
            "reason": f"Adaptive search (radius ±{min(radius, max_radius)}, {len(target_records)} records) yielded theoretical price ₹{theoretical_price:.0f}. Applied strict non-negative floor.",
            "evidence": {
                "search_radius": min(radius, max_radius),
                "records_found": len(target_records),
                "anchor_guests": float(anchor_guests),
                "anchor_price": float(anchor_price),
                "slope": float(slope),
                "raw_adjustment": float(raw_adj)
            }
        }
