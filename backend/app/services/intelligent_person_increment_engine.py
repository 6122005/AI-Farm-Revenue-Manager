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
            
        # 2. Helper to calculate theoretical price for a specific guest count
        def calc_theoretical_for_g(g: int) -> float:
            radius = 0
            max_radius = 5
            target_records = pd.DataFrame()
            
            while radius <= max_radius:
                lower_bound = g - radius
                upper_bound = g + radius
                target_records = df[(df['person_count'] >= lower_bound) & (df['person_count'] <= upper_bound)]
                if len(target_records) >= 8:
                    break
                radius += 1
                
            if target_records.empty:
                target_records = df
                
            anchor_guests = target_records['person_count'].mean()
            anchor_price = target_records['selling_price'].median()
            
            return anchor_price + slope * (g - anchor_guests)
            
        # 3. Monotonic Enforcement: Ensure price never drops as guests increase
        max_theoretical_price = base_price
        for k in range(1, req_guests + 1):
            t_price = calc_theoretical_for_g(k)
            if t_price > max_theoretical_price:
                max_theoretical_price = t_price
                
        theoretical_price = max_theoretical_price
        
        # 4. Strict Additive Rule (Never subtract from Base Price)
        raw_adj = theoretical_price - base_price
        adj = float(max(0.0, raw_adj))
        
        return {
            "adjustment_amount": adj,
            "reason": f"Monotonic adaptive search yielded maximum theoretical price ₹{theoretical_price:.0f}. Applied strict non-negative floor.",
            "evidence": {
                "slope": float(slope),
                "raw_adjustment": float(raw_adj)
            }
        }
