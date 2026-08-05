import pandas as pd
import numpy as np
import time
from typing import Optional, Tuple, Dict, Any
from app.services.slot_engine import slot_engine

class HistoricalSlotRelationshipEngine:
    _cache_time = 0
    _relationships_cache = None

    @classmethod
    def get_season(cls, month: int) -> str:
        if month in [3, 4, 5, 6]:
            return 'summer'
        elif month in [7, 8, 9, 10]:
            return 'monsoon'
        else:
            return 'winter'

    @classmethod
    def get_related_slot(cls, slot: str) -> Optional[str]:
        norm_slot = slot_engine.normalize_commercial_slot(slot)
        if norm_slot == "24H Day": return "24H Night"
        if norm_slot == "24H Night": return "24H Day"
        if norm_slot == "12H Day": return "12H Night"
        if norm_slot == "12H Night": return "12H Day"
        return None

    @classmethod
    def _learn_relationships(cls) -> Dict[str, Any]:
        try:
            from app.services.prediction_engine import prediction_engine
            df = prediction_engine.get_clean_data()
            if df.empty:
                return {}
        except Exception:
            return {}

        # 1. Filter out festivals and relatives/comps
        df = df[(df['is_festival'] == 0) & (df['selling_price'] >= 500)].copy()
        if df.empty:
            return {}

        df['norm_slot'] = df['commercial_slot'].apply(slot_engine.normalize_commercial_slot)
        df['season'] = df['month'].apply(cls.get_season)

        # 2. IQR Outlier Filtering globally per slot
        cleaned_dfs = []
        for s in df['norm_slot'].unique():
            sub = df[df['norm_slot'] == s].copy()
            q1 = sub['selling_price'].quantile(0.25)
            q3 = sub['selling_price'].quantile(0.75)
            iqr = q3 - q1
            sub = sub[(sub['selling_price'] >= q1 - 1.5*iqr) & (sub['selling_price'] <= q3 + 1.5*iqr)]
            cleaned_dfs.append(sub)
            
        if not cleaned_dfs:
            return {}
        df = pd.concat(cleaned_dfs)

        # Grouping for relationship pairings (Year is ignored to aggregate historical patterns)
        # We need pairs of bookings. To pair them robustly, we calculate medians at various granularities.
        # Wait, the user said: "Calculate median price for each slot grouped by (Month, Weekday/Weekend, Season)"
        
        # We calculate the medians grouped by Month and Weekend
        grouped = df.groupby(['season', 'month', 'is_weekend', 'norm_slot'])['selling_price'].median().reset_index()
        
        # Pivot so we can compare slots directly
        pivot = grouped.pivot(index=['season', 'month', 'is_weekend'], columns='norm_slot', values='selling_price').reset_index()
        
        pairs = [("24H Day", "24H Night"), ("24H Night", "24H Day"), ("12H Day", "12H Night"), ("12H Night", "12H Day")]
        
        relationships = {}
        
        for slot_req, slot_rel in pairs:
            if slot_req not in pivot.columns or slot_rel not in pivot.columns:
                continue
                
            sub_pivot = pivot.dropna(subset=[slot_req, slot_rel]).copy()
            if sub_pivot.empty:
                continue
                
            sub_pivot['ratio'] = sub_pivot[slot_req] / sub_pivot[slot_rel]
            sub_pivot['diff'] = sub_pivot[slot_req] - sub_pivot[slot_rel]
            
            # Helper to calculate stats and choose the best method
            def get_stats(df_slice):
                if df_slice.empty: return None
                
                # Ratio stats
                ratio_mean = df_slice['ratio'].mean()
                ratio_std = df_slice['ratio'].std()
                ratio_cv = (ratio_std / ratio_mean) if ratio_mean != 0 else float('inf')
                
                # Diff stats
                diff_mean = df_slice['diff'].mean()
                diff_std = df_slice['diff'].std()
                diff_cv = (diff_std / abs(diff_mean)) if diff_mean != 0 else float('inf')
                
                # We need at least 2 points for std, else we assume 0 variance (high stability but low confidence)
                if pd.isna(ratio_std): ratio_cv = 0.0
                if pd.isna(diff_std): diff_cv = 0.0
                
                # Choose most stable method
                method = "RATIO" if ratio_cv <= diff_cv else "ABSOLUTE_DIFF"
                
                # Calculate final robust values using Median to avoid edge cases
                median_ratio = df_slice['ratio'].median()
                median_diff = df_slice['diff'].median()
                
                return {
                    "method": method,
                    "ratio": float(median_ratio),
                    "diff": float(median_diff),
                    "std": float(ratio_std if method == "RATIO" else diff_std),
                    "cv": float(ratio_cv if method == "RATIO" else diff_cv),
                    "samples": len(df_slice)
                }

            # Global
            global_stats = get_stats(sub_pivot)
            
            # Seasonal
            seasonal_stats = {}
            for season in ['summer', 'winter', 'monsoon']:
                season_slice = sub_pivot[sub_pivot['season'] == season]
                st = get_stats(season_slice)
                if st: seasonal_stats[season] = st
                
            # Monthly
            monthly_stats = {}
            for m in range(1, 13):
                m_slice = sub_pivot[sub_pivot['month'] == m]
                st = get_stats(m_slice)
                if st: monthly_stats[m] = st
                
            relationships[slot_req] = {
                "global": global_stats,
                "seasonal": seasonal_stats,
                "monthly": monthly_stats
            }
            
        return relationships

    @classmethod
    def get_relationships(cls):
        if cls._relationships_cache is None or time.time() - cls._cache_time > 3600:
            cls._relationships_cache = cls._learn_relationships()
            cls._cache_time = time.time()
        return cls._relationships_cache

    @classmethod
    def calculate_correction(
        cls, 
        requested_slot: str, 
        target_month: int, 
        ml_predicted_price: float,
        df_target_month: pd.DataFrame
    ) -> Tuple[float, str, str, str, float]:
        """
        Returns:
        (capped_correction, method_used, relationship_source, related_slot, historical_value)
        """
        norm_slot = slot_engine.normalize_commercial_slot(requested_slot)
        related_slot = cls.get_related_slot(norm_slot)
        if not related_slot:
            return 0.0, "NONE", "NONE", "NONE", 0.0
            
        relationships = cls.get_relationships()
        if norm_slot not in relationships:
            return 0.0, "NONE", "NONE", "NONE", 0.0
            
        rel_data = relationships[norm_slot]
        season = cls.get_season(target_month)
        
        # 1. Select the relationship source based on availability
        # Note: We prefer Monthly > Seasonal > Global. We require at least 2 samples for a valid relationship.
        chosen_stats = None
        source = "NONE"
        
        if target_month in rel_data['monthly'] and rel_data['monthly'][target_month]['samples'] >= 2:
            chosen_stats = rel_data['monthly'][target_month]
            source = "Monthly"
        elif season in rel_data['seasonal'] and rel_data['seasonal'][season]['samples'] >= 3:
            chosen_stats = rel_data['seasonal'][season]
            source = "Seasonal"
        elif rel_data['global'] and rel_data['global']['samples'] >= 5:
            chosen_stats = rel_data['global']
            source = "Global"
            
        if not chosen_stats:
            return 0.0, "NONE", "NONE", "NONE", 0.0
            
        # 2. Get Historical Median of the Related Slot for the specific requested month
        # We look into df_target_month for the related_slot.
        df_rel = df_target_month[df_target_month['commercial_slot'].apply(slot_engine.normalize_commercial_slot) == related_slot]
        if df_rel.empty:
            return 0.0, "NONE", "NONE", "NONE", 0.0
            
        related_median_price = df_rel['selling_price'].median()
        if pd.isna(related_median_price) or related_median_price <= 0:
            return 0.0, "NONE", "NONE", "NONE", 0.0
            
        # 3. Calculate Target Commercial Price
        method = chosen_stats['method']
        if method == "RATIO":
            target_commercial_price = related_median_price * chosen_stats['ratio']
            hist_val = chosen_stats['ratio']
        else:
            target_commercial_price = related_median_price + chosen_stats['diff']
            hist_val = chosen_stats['diff']
            
        # 4. Calculate Raw Correction
        raw_correction = target_commercial_price - ml_predicted_price
        
        # 5. Bound the Correction (±15% of ML prediction)
        max_correction = ml_predicted_price * 0.15
        capped_correction = max(min(raw_correction, max_correction), -max_correction)
        
        return float(capped_correction), method, source, related_slot, float(hist_val)

slot_relationship_engine = HistoricalSlotRelationshipEngine()
