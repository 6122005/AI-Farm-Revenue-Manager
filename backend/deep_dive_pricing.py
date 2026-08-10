from app.services.prediction_engine import PredictionEngine
from app.services.retrieval_engine import SimilarBookingRetriever
from app.services.intelligent_person_increment_engine import IntelligentPersonIncrementEngine
from app.services.historical_adjustments import HistoricalAdjustments
from app.services.commercial_optimizer import CommercialOptimizer
import pandas as pd

engine = PredictionEngine()
df_clean = engine.get_clean_data()

def debug_scenario(scenario_name, req):
    print(f"\n{'='*50}\nSCENARIO: {scenario_name}\n{'='*50}")
    
    # 1. Retrieval
    req_dict = engine._parse_request(req)
    context = SimilarBookingRetriever.retrieve(req_dict, df_clean)
    rep_price = context.base_price
    
    print(f"[1] Base Representative Price: ₹{rep_price:.2f}")
    print(f"    Retrieval Confidence: {context.confidence}%")
    print(f"    Fallback History: {context.fallback_history}")
    print(f"    Metadata: {context.metadata}")
    
    # 2. Guest Increment
    guest_adj = IntelligentPersonIncrementEngine.calculate_guest_increment(context)
    print(f"[2] Guest Adjustment ({req_dict.get('person_count')} guests): ₹{guest_adj['adjustment_amount']:.2f}")
    print(f"    Reason: {guest_adj['reason']}")
    
    # 3. Lead Time Adjustment
    lead_adj = HistoricalAdjustments.calculate_lead_days_adjustment(context)
    print(f"[3] Lead Days Adjustment ({req_dict.get('lead_days')} days): ₹{lead_adj['adjustment_amount']:.2f}")
    print(f"    Reason: {lead_adj['reason']}")
    
    # Base calculated fair price before ML and Commercial
    fair_price = rep_price + guest_adj['adjustment_amount'] + lead_adj['adjustment_amount']
    print(f"\n[Fair Price before ML/Optimization]: ₹{fair_price:.2f}")
    
    # 4. Commercial Optimization
    is_weekend = req_dict.get('is_weekend', 0)
    opt_res = CommercialOptimizer.optimize_price(
        fair_price=fair_price,
        booking_count=context.booking_count,
        competitor_price=0.0,
        is_weekend=bool(is_weekend),
        is_festival=False
    )
    print(f"[4] Commercial Optimization: +₹{opt_res['commercial_optimization_amount']:.2f}")
    print(f"    Reason: {opt_res['reason']}")
    print(f"[Final Output Estimate]: ₹{opt_res['revenue_optimized_price']:.2f}")

# Scenario 1: April 12H Day Weekend (High Weekend Price)
req1 = {
    "start_datetime": "2026-04-04 07:00",
    "end_datetime": "2026-04-04 19:00",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "lead_days": 3
}
debug_scenario("April 12H Day Weekend", req1)

# Scenario 2: Nov 24H Night Weekday (High Weekday Price)
req2 = {
    "start_datetime": "2026-11-04 19:00",
    "end_datetime": "2026-11-05 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3
}
debug_scenario("November 24H Night Weekday", req2)

