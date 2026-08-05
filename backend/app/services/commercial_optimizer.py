from typing import Dict, Any
from app.config_manager import ConfigManager

class CommercialOptimizer:
    """
    Commercial Optimization Layer
    This layer optimizes revenue beyond the ML 'fair market' price.
    In the future, it will use real elasticity (booking-attempt, conversion-rate, occupancy).
    Currently, it uses historical booking volume density to simulate demand elasticity.
    """
    
    @classmethod
    def optimize_price(
        cls, 
        fair_price: float, 
        booking_count: int, 
        competitor_price: float, 
        is_weekend: bool, 
        is_festival: bool
    ) -> Dict[str, Any]:
        
        max_surge = ConfigManager.get_rule("maximum_surge_multiplier", 1.5)
        
        # Simulated elasticity variables (Placeholder for future real elasticity data)
        # If the historical segment has > 20 records, we assume high market liquidity.
        # If it's a weekend or festival, demand is inherently more inelastic (people will pay).
        
        surge_multiplier = 1.0
        optimization_reason = "No commercial optimization applied."
        
        if booking_count > 20:
            if is_festival:
                surge_multiplier = min(max_surge, 1.15)
                optimization_reason = "High historical volume on Festival. Applied 15% revenue surge."
            elif is_weekend:
                surge_multiplier = min(max_surge, 1.08)
                optimization_reason = "High historical volume on Weekend. Applied 8% revenue surge."
            else:
                surge_multiplier = min(max_surge, 1.03)
                optimization_reason = "High historical volume on Weekday. Applied 3% revenue surge."
                
        # Competitor anchoring
        if competitor_price > fair_price * surge_multiplier:
            # We can afford to push a little closer to competitor
            potential_upside = (competitor_price - (fair_price * surge_multiplier)) * 0.3
            optimized = (fair_price * surge_multiplier) + potential_upside
            optimization_reason += f" Anchored towards higher competitor price (+₹{potential_upside:.0f})."
        else:
            optimized = fair_price * surge_multiplier
            
        return {
            "revenue_optimized_price": float(optimized),
            "commercial_optimization_amount": float(optimized - fair_price),
            "reason": optimization_reason
        }
