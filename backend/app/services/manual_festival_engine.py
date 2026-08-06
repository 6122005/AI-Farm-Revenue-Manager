import pandas as pd
import datetime
import os
from typing import Dict, Any

class ManualFestivalEngine:
    _festival_cache = None
    _last_modified_time = None
    
    @classmethod
    def _load_festivals(cls):
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "Farm_Booking_Data_new.xlsx")
        
        # Check if file has been modified since we last cached it
        try:
            current_mtime = os.path.getmtime(data_path)
        except OSError:
            current_mtime = 0
            
        if cls._festival_cache is not None and cls._last_modified_time == current_mtime:
            return cls._festival_cache
        
        try:
            df = pd.read_excel(data_path, sheet_name="Sheet4")
            
            # Create a dictionary mapping Date (string YYYY-MM-DD) to Multiplier and Name
            festivals = {}
            for idx, row in df.iterrows():
                try:
                    # Convert date to string YYYY-MM-DD
                    if pd.notna(row.get('Date')):
                        dt_obj = pd.to_datetime(row['Date'])
                        date_str = dt_obj.strftime("%Y-%m-%d")
                        
                        # Get multiplier (default to 1.0 if not found)
                        multiplier = float(row.get('multiplier', 1.0))
                        if pd.isna(multiplier):
                            multiplier = 1.0
                            
                        festivals[date_str] = {
                            "name": str(row.get('Festival_Name', 'Holiday')),
                            "multiplier": multiplier
                        }
                except Exception as e:
                    continue
                    
            cls._festival_cache = festivals
            cls._last_modified_time = current_mtime
            return cls._festival_cache
            
        except Exception as e:
            print(f"Error loading festivals: {e}")
            return {}
            
    @classmethod
    def calculate_premium(cls, booking_date_str: str, base_price: float) -> Dict[str, Any]:
        """
        Reads Sheet4. If booking_date_str matches a festival date, applies the multiplier.
        """
        festivals = cls._load_festivals()
        
        if booking_date_str in festivals:
            fest_info = festivals[booking_date_str]
            multiplier = fest_info["multiplier"]
            
            # If multiplier is 2.0, the adjustment is (2.0 - 1) * base_price = 1.0 * base_price
            if multiplier > 1.0:
                adjustment = base_price * (multiplier - 1.0)
                reason = f"Date matches festival '{fest_info['name']}'. Applied custom multiplier of {multiplier}x from Excel."
                return {
                    "adjustment_amount": float(adjustment),
                    "reason": reason
                }
                
        # If no match or multiplier <= 1.0, return 0
        return {
            "adjustment_amount": 0.0,
            "reason": "Date is not listed as a festival in Excel, or no multiplier is set."
        }
