import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.config import DATA_DIR
import logging

logger = logging.getLogger(__name__)

class FestivalEngine:
    _instance = None
    _is_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FestivalEngine, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not self._is_initialized:
            self.file_path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
            self.festivals_df = pd.DataFrame()
            self.reload_cache()
            self.__class__._is_initialized = True

    def reload_cache(self):
        """Loads Sheet4 from the single source of truth Excel file into memory."""
        try:
            if not self.file_path.exists():
                logger.warning(f"Festival file not found at {self.file_path}")
                return

            df = pd.read_excel(self.file_path, sheet_name="Sheet4")
            
            # Ensure proper datetime types
            df['window_start'] = pd.to_datetime(df['window_start'])
            df['window_end'] = pd.to_datetime(df['window_end'])
            df['festival_date'] = pd.to_datetime(df['festival_date'])
            
            # Ensure multiplier is float
            df['dynamic_multiplier'] = df['dynamic_multiplier'].astype(float)
            
            self.festivals_df = df
            logger.info(f"Loaded {len(self.festivals_df)} festivals from Sheet4.")
        except Exception as e:
            logger.error(f"Failed to load festival cache from Sheet4: {e}")
            self.festivals_df = pd.DataFrame()

    def _get_overlap_hours(self, start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> float:
        """Calculates overlap between two time intervals in hours."""
        latest_start = max(start1, start2)
        earliest_end = min(end1, end2)
        delta = (earliest_end - latest_start).total_seconds()
        return max(0.0, delta / 3600.0)

    def detect_festivals(self, check_in: datetime, check_out: datetime) -> Dict[str, Any]:
        """
        Intelligent interval overlap detection.
        Returns the 15 ML features required by the system.
        """
        booking_hours = (check_out - check_in).total_seconds() / 3600.0
        if booking_hours <= 0:
            booking_hours = 24.0 # Fallback
            
        default_features = {
            "festival_detected": False,
            "festival_name": "None",
            "festival_category": "None",
            "festival_tier": "None",
            "festival_demand_level": "None",
            "festival_multiplier": 1.0,
            "festival_overlap_hours": 0.0,
            "festival_overlap_percentage": 0.0,
            "festival_window_start": None,
            "festival_window_end": None,
            "days_before_festival": 365,
            "days_after_festival": 365,
            "is_peak_festival": False,
            "multiple_festival_overlap": False,
            "highest_priority_festival": "None",
            
            # Backward compatibility
            "is_festival": 0
        }

        if self.festivals_df.empty:
            return default_features

        overlapping_festivals = []
        
        # Calculate days to closest future/past festivals for the non-overlap features
        min_days_before = 365
        min_days_after = 365

        for _, row in self.festivals_df.iterrows():
            w_start = row['window_start']
            w_end = row['window_end']
            
            # Distance metrics
            if w_start > check_out:
                days_before = (w_start - check_out).days
                if days_before < min_days_before:
                    min_days_before = days_before
            elif check_in > w_end:
                days_after = (check_in - w_end).days
                if days_after < min_days_after:
                    min_days_after = days_after
            
            overlap_hrs = self._get_overlap_hours(check_in, check_out, w_start, w_end)
            if overlap_hrs > 0:
                overlapping_festivals.append({
                    "name": row.get('festival_name', 'Unknown'),
                    "overlap_hrs": overlap_hrs,
                    "multiplier": float(row.get('dynamic_multiplier', 1.0)),
                    "category": str(row.get('category', 'Standard')),
                    "tier": str(row.get('festival_tier', 'Tier 2')),
                    "demand_level": str(row.get('demand_level', 'High')),
                    "w_start": w_start,
                    "w_end": w_end
                })
        
        default_features["days_before_festival"] = min_days_before
        default_features["days_after_festival"] = min_days_after

        if not overlapping_festivals:
            return default_features

        # We have overlaps! Find the highest multiplier.
        overlapping_festivals.sort(key=lambda x: x["multiplier"], reverse=True)
        primary = overlapping_festivals[0]
        
        default_features.update({
            "festival_detected": True,
            "festival_name": primary["name"],
            "festival_category": primary["category"],
            "festival_tier": primary["tier"],
            "festival_demand_level": primary["demand_level"],
            "festival_multiplier": primary["multiplier"],
            "festival_overlap_hours": round(primary["overlap_hrs"], 2),
            "festival_overlap_percentage": round((primary["overlap_hrs"] / booking_hours) * 100.0, 2),
            "festival_window_start": primary["w_start"].strftime("%Y-%m-%d %H:%M:%S"),
            "festival_window_end": primary["w_end"].strftime("%Y-%m-%d %H:%M:%S"),
            "days_before_festival": 0,
            "days_after_festival": 0,
            "is_peak_festival": bool(primary["tier"].lower() == "tier 1" or primary["multiplier"] >= 1.25),
            "multiple_festival_overlap": len(overlapping_festivals) > 1,
            "highest_priority_festival": primary["name"],
            
            # Backward compatibility
            "is_festival": 1
        })

        return default_features

# Global singleton instance
festival_engine = FestivalEngine()
