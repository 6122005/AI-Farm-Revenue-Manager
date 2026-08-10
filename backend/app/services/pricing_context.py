from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

class PricingContext:
    def __init__(self, request: Dict[str, Any], retrieved_segment: pd.DataFrame, stats: Dict[str, Any]):
        self.request = request
        self.retrieved_segment = retrieved_segment
        self.stats = stats
        self.base_price = stats.get("representative_price", 0.0)
        
    @property
    def level_used(self) -> int:
        return self.stats.get("level_used", 9)
        
    @property
    def borrowing_metadata(self) -> Dict[str, Any]:
        return self.stats.get("borrowing_metadata", {})
        
    @property
    def confidence(self) -> float:
        return float(self.stats.get("confidence", 0.0))
        
    @property
    def booking_count(self) -> int:
        return self.stats.get("booking_count", 0)
        
    def get_segment_mean(self, df_subset: pd.DataFrame) -> float:
        if df_subset.empty:
            return self.base_price
        prices = df_subset['selling_price'].values
        if len(prices) > 2:
            mean_val = np.mean(prices)
            mad = np.mean(np.abs(prices - mean_val))
            if mad > 0:
                is_outlier = np.abs(prices - mean_val) > (3 * mad)
                prices = prices[~is_outlier]
        return float(np.mean(prices)) if len(prices) > 0 else self.base_price
