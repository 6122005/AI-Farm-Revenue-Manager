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
                        
                        # Get multiplier case-insensitively
                        mult_col = next((c for c in row.keys() if str(c).lower() == 'multiplier'), None)
                        multiplier = float(row[mult_col]) if mult_col and pd.notna(row[mult_col]) else 1.0
                        
                        # Get name case-insensitively
                        name_col = next((c for c in row.keys() if 'name' in str(c).lower() or 'festival' in str(c).lower()), None)
                        name = str(row[name_col]) if name_col and pd.notna(row[name_col]) else "Holiday"
                            
                        festivals[date_str] = {
                            "name": name,
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
    def calculate_premium(cls, start_dt: datetime.datetime, end_dt: datetime.datetime, base_price: float) -> Dict[str, Any]:
        """
        Reads Sheet4. Checks all dates from start_dt to end_dt. 
        If any date matches a festival, applies the maximum multiplier found.
        """
        festivals = cls._load_festivals()
        
        current_date = start_dt.date()
        end_date = end_dt.date()
        
        max_multiplier = 1.0
        best_festival = None
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # If end_dt is exactly midnight, don't count the end_date unless it's also the start_date
            if current_date == end_date and end_dt.hour == 0 and end_dt.minute == 0 and start_dt.date() != end_date:
                break
                
            if date_str in festivals:
                fest_info = festivals[date_str]
                if fest_info["multiplier"] > max_multiplier:
                    max_multiplier = fest_info["multiplier"]
                    best_festival = fest_info
                    
            current_date += datetime.timedelta(days=1)
            
        if max_multiplier > 1.0 and best_festival:
            adjustment = base_price * (max_multiplier - 1.0)
            reason = f"Booking touches festival '{best_festival['name']}'. Applied custom multiplier of {max_multiplier}x from Excel."
            return {
                "adjustment_amount": float(adjustment),
                "reason": reason
            }
                
        return {
            "adjustment_amount": 0.0,
            "reason": "Date is not listed as a festival in Excel, or no multiplier is set."
        }
        
    @classmethod
    def is_festival_booking(cls, start_dt: datetime.datetime, end_dt: datetime.datetime) -> bool:
        """
        Returns True if the booking overlaps with any festival date.
        """
        festivals = cls._load_festivals()
        current_date = start_dt.date()
        end_date = end_dt.date()
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            if current_date == end_date and end_dt.hour == 0 and end_dt.minute == 0 and start_dt.date() != end_date:
                break
                
            if date_str in festivals:
                return True
                
            current_date += datetime.timedelta(days=1)
            
        return False
