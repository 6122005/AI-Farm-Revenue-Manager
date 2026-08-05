from typing import Dict, Any, Callable
import numpy as np

class ExtendedStayEngine:
    """
    Engine to handle custom duration slots (e.g. 36H, 77H, 120H).
    Implements Block Decomposition and Length of Stay (LOS) volume discounting.
    """

    @classmethod
    def process_custom_duration(
        cls, 
        duration_hours: float, 
        request_data: Dict[str, Any], 
        predict_fn: Callable[[Dict[str, Any], bool], Dict[str, Any]],
        is_batch: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates price for a custom duration by breaking it into 24H blocks + residual hours.
        Calls predict_fn (usually prediction_engine.predict) to get the base 24H rate.
        """
        
        full_days = int(duration_hours // 24)
        residual_hours = duration_hours % 24
        
        # If it's less than 24 hours but not standard (e.g. 15H), we treat 0 full days and 15 residual, 
        # or we just use 24H rate as a ceiling.
        # But generally this is meant for > 24H.
        if full_days == 0 and residual_hours > 0:
            full_days = 1
            residual_hours = 0
            
        # Get base price for a standard 24H slot (assume 24H Night as default 24H anchor)
        anchor_req = dict(request_data)
        
        # Determine if it's weekend or not from original request
        # For simplicity of anchor, we use 24H Night which is the standard full day block
        anchor_req["commercial_slot"] = "24H Night"
        anchor_req["skip_extended_engine"] = True # Prevent infinite loop
        
        base_res = predict_fn(anchor_req, is_batch)
        base_24h_price = base_res.get("recommended_price", 0.0)
        
        if base_24h_price == 0.0:
            base_24h_price = base_res.get("base_price", 0.0)
            
        # Block Decomposition
        total_block_price = full_days * base_24h_price
        
        # Residual Calculation (20% premium on hourly rate for loose hours)
        hourly_rate = base_24h_price / 24.0
        residual_premium = 1.20
        residual_price = residual_hours * hourly_rate * residual_premium
        
        raw_total_price = total_block_price + residual_price
        
        # Extract market variables from prediction context
        festival_name = base_res.get("festival_name", "No Festival")
        is_festival = bool(festival_name and festival_name != "No Festival")
        occupancy = float(base_res.get("expected_occupancy_pct", 50.0))
        demand_score = float(base_res.get("demand_score", 50.0))
        lead_days = int(base_res.get("lead_days", 7))
        
        # Dynamic LOS Discount Rules
        raw_discount_pct = cls.get_los_discount(duration_hours)
        discount_pct = raw_discount_pct
        discount_reason = "LOS Volume Discount applied dynamically"
        
        if raw_discount_pct > 0:
            if is_festival:
                discount_pct = 0.0
                discount_reason = f"LOS Discount skipped due to Festival ({festival_name})"
            elif occupancy > 90.0:
                discount_pct = 0.0
                discount_reason = f"LOS Discount skipped due to High Occupancy (>{occupancy}%)"
            elif demand_score > 85.0:
                discount_pct = 0.0
                discount_reason = f"LOS Discount skipped due to High Demand Score (>{demand_score})"
            elif lead_days < 3:
                discount_pct = 0.0
                discount_reason = f"LOS Discount skipped due to Last-Minute Booking (< 3 Days)"
        
        discount_amount = raw_total_price * (discount_pct / 100.0)
        
        final_price = raw_total_price - discount_amount
        final_price_rounded = float(np.round(final_price, -2))
        
        explanation = (
            f"Extended Stay Breakdown ({duration_hours}H):\n"
            f"- Base 24H Block Price: ₹{base_24h_price:,.0f}\n"
            f"- Full Blocks: {full_days} (₹{total_block_price:,.0f})\n"
            f"- Residual Hours: {residual_hours}H (₹{residual_price:,.0f} at premium)\n"
            f"- Raw Total: ₹{raw_total_price:,.0f}\n"
            f"- LOS Policy: {discount_pct}% (-₹{discount_amount:,.0f}) | Reason: {discount_reason}\n"
            f"- Final Optimized Price: ₹{final_price_rounded:,.0f}"
        )
        
        return {
            "predicted_price": final_price_rounded, # Standard format for API
            "recommended_price": final_price_rounded,
            "base_price": raw_total_price,
            "commercial_slot": f"{duration_hours}H Extended",
            "explanation": explanation,
            "confidence_scores": base_res.get("confidence_scores", {}),
            "features_used": base_res.get("features_used", {})
        }

    @staticmethod
    def get_los_discount(duration_hours: float) -> float:
        if duration_hours >= 120:
            return 18.0
        elif duration_hours >= 72:
            return 12.0
        elif duration_hours >= 48:
            return 8.0
        elif duration_hours > 36:
            return 5.0
        return 0.0

    @staticmethod
    def parse_custom_slot(commercial_slot: str) -> float:
        """
        Parses strings like '77H', '36 Hours', '120h' into floats.
        Returns 0.0 if not parsed.
        """
        s = commercial_slot.strip().upper()
        if "H" in s:
            try:
                num = s.split("H")[0].strip()
                return float(num)
            except:
                pass
        return 0.0
        
extended_stay_engine = ExtendedStayEngine()
