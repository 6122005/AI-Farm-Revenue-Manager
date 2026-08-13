import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

class HistoricalPricingBaseline:
    
    @classmethod
    def fit_predict_expanding(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates leakage-safe expanding baselines.
        """
        if "booking_date" not in df.columns or "start_datetime" not in df.columns:
            return df
            
        df = df.copy()
        df["booking_date_dt"] = pd.to_datetime(df["booking_date"], errors="coerce")
        df["start_datetime_dt"] = pd.to_datetime(df["start_datetime"], errors="coerce")
        
        # Sort by booking_date to prevent future leakage
        df = df.sort_values(by="booking_date_dt").copy()
        df = df.reset_index(drop=False)
        original_idx = df["index"]
        
        # We will iterate and build knowledge up to index i (exclusive)
        # But for speed, we can use grouped expanding medians, but since dates can repeat, 
        # doing it purely iteratively in Python might be slow.
        # Let's vectorize it safely using shift and expanding on grouped sorted data.
        
        baseline_prices = []
        baseline_levels = []
        evidence_counts = []
        confidences = []
        
        # Pre-compute categorical mappings for speed
        df["cat_upper"] = df["commercial_slot"].astype(str).str.upper()
        df["guest_band"] = pd.cut(df["person_count"], bins=[0, 4, 10, 20, 100], labels=["1-4", "5-10", "11-20", "20+"], right=True).astype(str)
        df["season_str"] = df.get("season", np.where(df["month"].isin([3, 4, 5]), "SUMMER", np.where(df["month"].isin([11, 12, 1, 2]), "WINTER", "MONSOON"))).astype(str).str.upper()
        df["dur_band"] = pd.cut(df["duration_hours"], bins=[-1, 5.5, 8.5, 12.5, 18.5, 24.5, 100], labels=["1-5H", "6-8H", "9-12H", "13-18H", "19-24H", "24H+"]).astype(str)
        
        # To avoid python looping over 700 rows taking too long, let's just do a simple loop, 700 rows is instant.
        prices = df["selling_price"].values
        months = df["month"].values
        cats = df["cat_upper"].values
        weekends = df["is_weekend"].values
        guests = df["guest_band"].values
        couples = df["is_couple"].values
        seasons = df["season_str"].values
        vacations = df.get("is_vacation", pd.Series([0]*len(df))).values
        durs = df["dur_band"].values
        dur_hours = df["duration_hours"].values
        
        for i in range(len(df)):
            if i == 0:
                baseline_prices.append(np.nan)
                baseline_levels.append(9)
                evidence_counts.append(0)
                confidences.append("INSUFFICIENT")
                continue
                
            # History is 0 to i-1
            # We filter for valid prices > 0
            hist_mask = (prices[:i] > 0)
            if not hist_mask.any():
                baseline_prices.append(np.nan)
                baseline_levels.append(9)
                evidence_counts.append(0)
                confidences.append("INSUFFICIENT")
                continue
                
            h_prices = prices[:i][hist_mask]
            h_months = months[:i][hist_mask]
            h_cats = cats[:i][hist_mask]
            h_weekends = weekends[:i][hist_mask]
            h_guests = guests[:i][hist_mask]
            h_vacations = vacations[:i][hist_mask]
            h_seasons = seasons[:i][hist_mask]
            h_durs = durs[:i][hist_mask]
            h_couples = couples[:i][hist_mask]
            
            c_m = months[i]
            c_c = cats[i]
            c_w = weekends[i]
            c_g = guests[i]
            c_v = vacations[i]
            c_s = seasons[i]
            c_d = durs[i]
            c_couple = couples[i]
            c_dur_hour = dur_hours[i]
            
            # Level 1: Month x Category x Weekend x Guest x Duration x Vacation
            mask1 = (h_months == c_m) & (h_cats == c_c) & (h_weekends == c_w) & (h_guests == c_g) & (h_durs == c_d) & (h_vacations == c_v)
            # Level 2: Month x Category x Weekend x Vacation
            mask2 = (h_months == c_m) & (h_cats == c_c) & (h_weekends == c_w) & (h_vacations == c_v)
            # Level 3: Month x Category x Weekend x Guest
            mask3 = (h_months == c_m) & (h_cats == c_c) & (h_weekends == c_w) & (h_guests == c_g)
            # Level 4: Month x Category x Weekend
            mask4 = (h_months == c_m) & (h_cats == c_c) & (h_weekends == c_w)
            # Level 5: Month x Category
            mask5 = (h_months == c_m) & (h_cats == c_c)
            # Level 6: Season x Category x Weekend
            mask6 = (h_seasons == c_s) & (h_cats == c_c) & (h_weekends == c_w)
            # Level 7: Category x Weekend
            mask7 = (h_cats == c_c) & (h_weekends == c_w)
            # Level 8: Category
            mask8 = (h_cats == c_c)
            
            masks = [mask1, mask2, mask3, mask4, mask5, mask6, mask7, mask8, np.ones(len(h_prices), dtype=bool)]
            
            found = False
            for lvl_idx, mask in enumerate(masks):
                lvl = lvl_idx + 1 # 1-indexed for logging
                count = mask.sum()
                if count >= 3:
                    found = True
                    med_price = np.median(h_prices[mask])
                    
                    # Apply Duration Proportional Scaling if mask didn't explicitly include duration
                    # (Level 1, 2 include duration band matching natively)
                    if lvl > 2:
                        slot = str(c_c).upper()
                        if "12H" in slot or "DAY" in slot and "24H" not in slot and "EXTENDED" not in slot:
                            std_dur = 5.0 if "COUPLE" in slot else 12.0
                        elif "24H" in slot or "EXTENDED" in slot:
                            std_dur = 24.0
                        elif "COUPLE HALF DAY" in slot:
                            std_dur = 5.0
                        else:
                            std_dur = 24.0
                            
                        # If requested duration is significantly less, apply 50% fixed 50% variable logic
                        if c_dur_hour > 0 and c_dur_hour <= std_dur - 1.5:
                            fixed_portion = med_price * 0.5
                            var_portion = med_price * 0.5
                            hourly_rate = var_portion / std_dur
                            med_price = fixed_portion + (hourly_rate * c_dur_hour)

                    baseline_prices.append(med_price)
                    baseline_levels.append(lvl)
                    evidence_counts.append(count)
                    
                    if count >= 15: conf = "VERY STRONG"
                    elif count >= 8: conf = "STRONG"
                    elif count >= 5: conf = "MEDIUM"
                    else: conf = "WEAK"
                    
                    confidences.append(conf)
                    break
                    
            if not found:
                baseline_prices.append(np.median(h_prices))
                baseline_levels.append(7)
                evidence_counts.append(len(h_prices))
                confidences.append("GLOBAL_FALLBACK")
                
        df["historical_baseline_price"] = baseline_prices
        df["baseline_level"] = baseline_levels
        df["baseline_evidence_count"] = evidence_counts
        df["baseline_confidence"] = confidences
        
        # Fill first row or un-fillables with global median of overall
        global_med = df["selling_price"][df["selling_price"]>0].median()
        df["historical_baseline_price"] = df["historical_baseline_price"].fillna(global_med)
        
        df = df.set_index("index").loc[original_idx].copy() # Restore original order if needed, but we keep sorted
        df.drop(columns=["cat_upper", "guest_band", "season_str"], inplace=True)
        return df
