import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from app.services.feature_engineering import FeatureEngineer
from app.services.pricing_context import PricingContext

class SimilarBookingRetriever:
    
    @classmethod
    def calculate_similarity_score(cls, request: Dict[str, Any], candidate: pd.Series) -> float:
        score = 100.0
        
        # Exact month match is crucial
        if request.get('month') != candidate.get('month'):
            score -= 20.0
            
        # Same weekend/weekday is crucial
        if request.get('is_weekend') != candidate.get('is_weekend'):
            score -= 25.0
            
        # Guest closeness
        req_guests = request.get('person_count', 4)
        can_guests = candidate.get('person_count', 4)
        if req_guests != can_guests:
            score -= abs(req_guests - can_guests) * 2.0
            
        # Lead time closeness (if inside the same bucket, it's good, otherwise penalty)
        req_lead = request.get('lead_days', 0)
        can_lead = candidate.get('lead_days', 0)
        lead_diff = abs(req_lead - can_lead)
        if lead_diff > 14:
            score -= 15.0
        elif lead_diff > 7:
            score -= 5.0
            
        return max(0.0, score)
        
    @classmethod
    def calculate_representative_price(cls, df_subset: pd.DataFrame) -> Dict[str, Any]:
        if df_subset.empty:
            return {
                "booking_count": 0,
                "median": 0.0,
                "trimmed_mean": 0.0,
                "variance": 0.0,
                "mad": 0.0,
                "cv": 0.0
            }
            
        prices = df_subset['selling_price'].values
        booking_count = len(prices)
        median_price = np.median(prices)
        
        mad = np.median(np.abs(prices - median_price))
        variance = np.var(prices) if booking_count > 1 else 0.0
        
        if booking_count > 2 and mad > 0:
            is_outlier = np.abs(prices - median_price) > (3 * mad)
            trimmed_prices = prices[~is_outlier]
            trimmed_mean = np.mean(trimmed_prices) if len(trimmed_prices) > 0 else median_price
        else:
            trimmed_mean = np.mean(prices)
            
        cv = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0.0
            
        return {
            "booking_count": booking_count,
            "median": float(median_price),
            "trimmed_mean": float(trimmed_mean),
            "variance": float(variance),
            "mad": float(mad),
            "cv": float(cv)
        }

    @classmethod
    def retrieve(cls, req: Dict[str, Any], df: pd.DataFrame) -> PricingContext:
        req_slot = req.get('commercial_slot', '12H Day')
        req_month = req.get('month', 1)
        req_weekend = req.get('is_weekend', 0)
        req_season = req.get('season', 'winter')

        # Base filter: Golden Rule (Never mix slots)
        df_slot = df[df['commercial_slot'] == req_slot].copy()

        insights = FeatureEngineer._load_insights()
        wk_premium = insights.get("weekend_premium_ratio", 1.25)
        sm_premium = insights.get("summer_demand_ratio", 1.20)
        wt_premium = insights.get("winter_demand_ratio", 1.00)
        
        season_multiplier = 1.0
        if req_season == "Summer": season_multiplier = sm_premium
        elif req_season == "Winter": season_multiplier = wt_premium

        candidates = pd.DataFrame()
        level_used = 0
        borrowing_metadata = None
        
        if not df_slot.empty:
            # Level 1: Same Month + Same Slot + Same Weekend
            l1 = df_slot[
                (df_slot['month'] == req_month) &
                (df_slot['is_weekend'] == req_weekend)
            ]
            if len(l1) >= 2: candidates, level_used = l1, 1
            
            # Level 2: Same Month + Opposite Weekend (Learn Ratio)
            if candidates.empty:
                l2 = df_slot[
                    (df_slot['month'] == req_month) &
                    (df_slot['is_weekend'] != req_weekend)
                ].copy()
                if len(l2) >= 2:
                    multiplier = wk_premium if req_weekend == 1 else (1.0 / wk_premium)
                    l2['selling_price'] = l2['selling_price'] * multiplier
                    candidates, level_used = l2, 2
                    borrowing_metadata = {
                        "borrowed_from": f"Same Month Opposite {'Weekday' if req_weekend else 'Weekend'}",
                        "multiplier": multiplier,
                        "reason": f"Base {'Weekday' if req_weekend else 'Weekend'} Price × Premium ({multiplier:.2f}x)"
                    }
                    
            # Level 3: Adjacent Month + Same Weekend
            if candidates.empty:
                l3 = df_slot[
                    ((df_slot['month'].between(req_month - 1, req_month + 1)) | 
                     ((req_month == 1) & (df_slot['month'] == 12)) | 
                     ((req_month == 12) & (df_slot['month'] == 1))) &
                    (df_slot['is_weekend'] == req_weekend)
                ]
                if len(l3) >= 2: candidates, level_used = l3, 3
                
            # Level 4: Same Season + Same Weekend
            if candidates.empty:
                l4 = df_slot[
                    (df_slot['season'] == req_season) &
                    (df_slot['is_weekend'] == req_weekend)
                ]
                if len(l4) >= 2: candidates, level_used = l4, 4
                
            # Level 5: Entire Year + Same Weekend
            if candidates.empty:
                l5 = df_slot[df_slot['is_weekend'] == req_weekend].copy()
                if len(l5) >= 2:
                    l5['selling_price'] = l5['selling_price'] * season_multiplier
                    candidates, level_used = l5, 5
                    borrowing_metadata = {
                        "borrowed_from": f"All Year Same {'Weekend' if req_weekend else 'Weekday'}",
                        "multiplier": season_multiplier,
                        "reason": f"Yearly Base Price × Season Premium ({season_multiplier:.2f}x)"
                    }
                    
            # Level 6: Entire Year + Opposite Weekend
            if candidates.empty:
                l6 = df_slot[df_slot['is_weekend'] != req_weekend].copy()
                if len(l6) >= 2:
                    wk_multiplier = wk_premium if req_weekend == 1 else (1.0 / wk_premium)
                    total_multiplier = season_multiplier * wk_multiplier
                    l6['selling_price'] = l6['selling_price'] * total_multiplier
                    candidates, level_used = l6, 6
                    borrowing_metadata = {
                        "borrowed_from": f"All Year Opposite {'Weekday' if req_weekend else 'Weekend'}",
                        "multiplier": total_multiplier,
                        "reason": f"Yearly Base Price × Season & Weekend Premium ({total_multiplier:.2f}x)"
                    }

        if candidates.empty:
            borrowing_metadata = {
                "borrowed_from": "Global Default",
                "multiplier": 1.0,
                "reason": "Absolute Fallback (No Slot Data)"
            }
            stats = {"level_used": 7, "borrowing_metadata": borrowing_metadata, "representative_price": 8500.0, "confidence": 0.0}
            return PricingContext(req, pd.DataFrame(), stats)
            
        # Score candidates
        candidates['similarity_score'] = candidates.apply(lambda row: cls.calculate_similarity_score(req, row), axis=1)
        candidates = candidates.sort_values('similarity_score', ascending=False)
        
        # We cap at 20 most similar bookings within the segment to avoid smoothing out local variance
        top_20 = candidates.head(20).copy()
        
        stats = cls.calculate_representative_price(top_20)
        stats['representative_price'] = stats.get('trimmed_mean', stats.get('median', 8500.0))
        stats['level_used'] = level_used
        
        # Rule 7: Low Reliability should only appear if less than 2 usable bookings exist after every borrowing level.
        if len(top_20) >= 2:
            if level_used <= 2: stats['confidence'] = 95.0
            elif level_used == 3: stats['confidence'] = 85.0
            elif level_used == 4: stats['confidence'] = 75.0
            elif level_used == 5: stats['confidence'] = 65.0
            elif level_used == 6: stats['confidence'] = 55.0
        else:
            stats['confidence'] = 0.0
            
        if borrowing_metadata:
            stats['borrowing_metadata'] = borrowing_metadata
            
        return PricingContext(req, top_20, stats)
