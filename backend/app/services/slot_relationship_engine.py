import pandas as pd
import numpy as np
import time
from typing import Optional, Tuple, Dict, Any
from app.services.slot_engine import slot_engine

class IntelligentSlotSimilarityEngine:
    _cache_time = 0
    _relationships_cache = None

    @classmethod
    def get_season(cls, month: int) -> str:
        if month in [3, 4, 5, 6]: return 'summer'
        if month in [7, 8, 9, 10]: return 'monsoon'
        return 'winter'

    @classmethod
    def _learn_relationships(cls) -> Dict[str, Any]:
        try:
            from app.services.prediction_engine import prediction_engine
            df = prediction_engine.get_clean_data()
            if df.empty:
                return {}
        except Exception:
            return {}

        # 1. Filter out festivals and extreme outliers for clean ratio learning
        df = df[(df['is_festival'] == 0) & (df['selling_price'] >= 500)].copy()
        if df.empty:
            return {}

        df['norm_slot'] = df['commercial_slot'].apply(slot_engine.normalize_commercial_slot)
        df['season'] = df['month'].apply(cls.get_season)



        def build_ratios(df_slice):
            means = df_slice.groupby('norm_slot')['selling_price'].mean()
            slots = ["12H Day", "12H Night", "24H Day", "24H Night"]
            ratios = {}
            for target in slots:
                ratios[target] = {}
                for source in slots:
                    if target in means and source in means and means[source] > 0:
                        ratios[target][source] = float(means[target] / means[source])
            return ratios

        global_ratios = build_ratios(df)

        monthly_ratios = {}
        for m in range(1, 13):
            monthly_ratios[m] = build_ratios(df[df['month'] == m])
            
        seasonal_ratios = {}
        for s in ['summer', 'winter', 'monsoon']:
            seasonal_ratios[s] = build_ratios(df[df['season'] == s])

        return {
            "global": global_ratios,
            "monthly": monthly_ratios,
            "seasonal": seasonal_ratios
        }

    @classmethod
    def get_relationships(cls):
        if cls._relationships_cache is None or time.time() - cls._cache_time > 3600:
            cls._relationships_cache = cls._learn_relationships()
            cls._cache_time = time.time()
        return cls._relationships_cache

    @classmethod
    def get_conversion_ratio(cls, target_slot: str, source_slot: str, month: int) -> Tuple[float, str]:
        """
        Returns (ratio, source_level)
        e.g., (0.50, 'monthly')
        """
        target = slot_engine.normalize_commercial_slot(target_slot)
        source = slot_engine.normalize_commercial_slot(source_slot)
        
        rels = cls.get_relationships()
        if not rels:
            return 1.0, "default"

        season = cls.get_season(month)

        # Level 1: Try Monthly Ratio
        if target in rels['monthly'].get(month, {}) and source in rels['monthly'][month][target]:
            ratio, level = rels['monthly'][month][target][source], "monthly"
        # Level 2: Try Seasonal Ratio
        elif target in rels['seasonal'].get(season, {}) and source in rels['seasonal'][season][target]:
            ratio, level = rels['seasonal'][season][target][source], "seasonal"
        # Level 3: Try Global Ratio
        elif target in rels['global'] and source in rels['global'][target]:
            ratio, level = rels['global'][target][source], "global"
        else:
            ratio, level = None, None
            
        if ratio is not None:
            # Apply user-requested cap: 24H -> 12H ratio must not exceed 0.55
            if "24H" in source and "12H" in target:
                ratio = min(ratio, 0.55)
            return ratio, level

        # Fallback bounds if completely missing
        if "24H" in source and "12H" in target: return 0.5, "fallback_heuristic"
        if "12H" in source and "24H" in target: return 2.0, "fallback_heuristic"
        return 1.0, "fallback_heuristic"

slot_relationship_engine = IntelligentSlotSimilarityEngine()
