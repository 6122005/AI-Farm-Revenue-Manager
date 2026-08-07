import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from app.services.feature_engineering import FeatureEngineer
from app.services.pricing_context import PricingContext
from app.services.slot_relationship_engine import slot_relationship_engine

class SimilarBookingRetriever:
    
    @classmethod
    def get_slot_similarity(cls, req_slot: str, can_slot: str) -> float:
        if not isinstance(req_slot, str) or not isinstance(can_slot, str):
            return 0.0
        if req_slot == can_slot:
            return 20.0
        if "24H" in req_slot and "24H" in can_slot:
            return 15.0
        if "12H" in req_slot and "12H" in can_slot:
            return 15.0
        if ("Day" in req_slot and "Day" in can_slot) or ("Night" in req_slot and "Night" in can_slot):
            return 10.0
        return 5.0
        
    @classmethod
    def calculate_similarity_score(cls, request: Dict[str, Any], candidate: pd.Series) -> float:
        score = 0.0
        
        # Month: 30%
        if request.get('month') == candidate.get('month'):
            score += 30.0
            
        # Weekend/Weekday: 25%
        if request.get('is_weekend') == candidate.get('is_weekend'):
            score += 25.0
            
        # Slot Similarity: 20%
        score += cls.get_slot_similarity(request.get('commercial_slot', ''), candidate.get('commercial_slot', ''))
            
        # Festival Tier: 10%
        req_fest = request.get('is_festival', 0)
        can_fest = candidate.get('is_festival', 0)
        if req_fest == can_fest:
            score += 10.0
            
        # Season Match: 5%
        req_season = slot_relationship_engine.get_season(request.get('month', 1))
        can_season = slot_relationship_engine.get_season(candidate.get('month', 1))
        if req_season == can_season:
            score += 5.0
            
        # Guest Count: 5%
        req_guests = request.get('person_count', 4)
        can_guests = candidate.get('person_count', 4)
        g_diff = abs(req_guests - can_guests)
        if g_diff == 0: score += 5.0
        elif g_diff <= 2: score += 3.0
        elif g_diff <= 5: score += 1.0
            
        # Lead Time: 5%
        req_lead = request.get('lead_days', 0)
        can_lead = candidate.get('lead_days', 0)
        l_diff = abs(req_lead - can_lead)
        if l_diff <= 7: score += 5.0
        elif l_diff <= 14: score += 3.0
        elif l_diff <= 30: score += 1.0
            
        return max(0.0, min(100.0, score))
        
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
        req_season = slot_relationship_engine.get_season(req_month)

        # Ensure base representative price never includes festival data to prevent skewing
        if "is_festival" in df.columns:
            df = df[df["is_festival"] == 0]

        candidates = pd.DataFrame()
        level_used = 0
        borrowing_metadata = None
        
        def find_closest_slot_data(pool_df, t_month):
            if pool_df.empty: return pd.DataFrame(), None
            # Find the best slot to borrow from
            # We score available slots based on slot_similarity
            unique_slots = pool_df['commercial_slot'].unique()
            best_slot = None
            best_sim = -1
            for s in unique_slots:
                sim = cls.get_slot_similarity(req_slot, s)
                if sim > best_sim:
                    best_sim = sim
                    best_slot = s
            if not best_slot: return pd.DataFrame(), None
            
            ratio, source_level = slot_relationship_engine.get_conversion_ratio(req_slot, best_slot, t_month)
            res_df = pool_df[pool_df['commercial_slot'] == best_slot].copy()
            res_df['selling_price'] = res_df['selling_price'] * ratio
            
            meta = {
                "borrowed_from": f"Slot Conversion: {best_slot} -> {req_slot}",
                "multiplier": ratio,
                "source_slot": best_slot,
                "reason": f"Learned {source_level} conversion ratio ({ratio:.2f}x)"
            }
            return res_df, meta

        # Level 1: Same Month + Same Weekend + Same Slot
        l1 = df[(df['month'] == req_month) & (df['is_weekend'] == req_weekend) & (df['commercial_slot'] == req_slot)]
        if len(l1) >= 2: candidates, level_used = l1, 1
        
        # Level 2: Same Month + Same Weekend + Closest Slot
        if candidates.empty:
            l2_pool = df[(df['month'] == req_month) & (df['is_weekend'] == req_weekend)]
            cands, meta = find_closest_slot_data(l2_pool, req_month)
            if len(cands) >= 2: candidates, level_used, borrowing_metadata = cands, 2, meta
                
        # Level 3: Same Season + Same Weekend + Same Slot
        if candidates.empty:
            l3 = df[(df['month'].apply(slot_relationship_engine.get_season) == req_season) & 
                    (df['is_weekend'] == req_weekend) & 
                    (df['commercial_slot'] == req_slot)]
            if len(l3) >= 2: candidates, level_used = l3, 3
            
        # Level 4: Same Season + Same Weekend + Closest Slot
        if candidates.empty:
            l4_pool = df[(df['month'].apply(slot_relationship_engine.get_season) == req_season) & 
                         (df['is_weekend'] == req_weekend)]
            cands, meta = find_closest_slot_data(l4_pool, req_month)
            if len(cands) >= 2: candidates, level_used, borrowing_metadata = cands, 4, meta
                
        # Level 5: Entire Year + Closest Slot (Prefer same weekend first, then any)
        if candidates.empty:
            l5_pool = df[df['is_weekend'] == req_weekend]
            if len(l5_pool) < 2:
                l5_pool = df # Absolute fallback
            cands, meta = find_closest_slot_data(l5_pool, req_month)
            if len(cands) >= 2: candidates, level_used, borrowing_metadata = cands, 5, meta

        if candidates.empty:
            borrowing_metadata = {
                "borrowed_from": "Pure ML Engine",
                "multiplier": 1.0,
                "source_slot": "None",
                "reason": "Absolute Fallback (No sufficient data found)"
            }
            stats = {"level_used": 6, "borrowing_metadata": borrowing_metadata, "representative_price": 8500.0, "confidence": 0.0}
            return PricingContext(req, pd.DataFrame(), stats)
            
        # Score candidates
        candidates['similarity_score'] = candidates.apply(lambda row: cls.calculate_similarity_score(req, row), axis=1)
        candidates = candidates.sort_values('similarity_score', ascending=False)
        
        # Cap at 20 most similar bookings
        top_20 = candidates.head(20).copy()
        
        stats = cls.calculate_representative_price(top_20)
        stats['representative_price'] = stats.get('trimmed_mean', stats.get('median', 8500.0))
        stats['level_used'] = level_used
        
        # Dynamic Confidence Score Redesign
        base_conf = 100.0
        
        # 1. Fallback Distance Penalty
        level_penalty = (level_used - 1) * 12.0
        base_conf -= level_penalty
        
        # 2. Sample Size Penalty
        sample_size = len(top_20)
        if sample_size < 10:
            base_conf -= (10 - sample_size) * 2.5
            
        # 3. Prediction Stability (CV Penalty)
        if sample_size > 1:
            mean_val = top_20['selling_price'].mean()
            std_val = top_20['selling_price'].std()
            if mean_val > 0:
                cv = std_val / mean_val
                if cv > 0.1:
                    cv_penalty = min(25.0, (cv - 0.1) * 100.0)
                    base_conf -= cv_penalty
                    
        # Clamp between 10% and 99.9%
        stats['confidence'] = round(max(10.0, min(99.9, base_conf)), 1)

        if borrowing_metadata:
            stats['borrowing_metadata'] = borrowing_metadata
            
        return PricingContext(req, top_20, stats)
