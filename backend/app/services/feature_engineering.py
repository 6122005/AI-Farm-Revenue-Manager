import pandas as pd
import json
import numpy as np
import joblib
import warnings
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from app.config import DATA_DIR
from app.services.slot_engine import slot_engine

FESTIVAL_CSV_PATH = DATA_DIR / "festivals.csv"

def load_festivals_dict() -> Tuple[Dict[str, str], Dict[str, float], List[str]]:
    fest_names = {}
    fest_mults = {}
    fest_eves = []
    
    if FESTIVAL_CSV_PATH.exists():
        try:
            df_f = pd.read_csv(FESTIVAL_CSV_PATH)
            for _, row in df_f.iterrows():
                d_str = str(row["date"]).strip()
                name = str(row.get("festival_name", "Festival"))
                mult = float(row.get("demand_multiplier", 1.25))
                is_eve = bool(row.get("is_eve", 0))

                fest_names[d_str] = name
                fest_mults[d_str] = mult

                try:
                    m_d = datetime.strptime(d_str, "%Y-%m-%d").strftime("%m-%d")
                    if m_d not in fest_names:
                        fest_names[m_d] = name
                        fest_mults[m_d] = mult
                    if is_eve:
                        fest_eves.append(m_d)
                except Exception:
                    pass

                if is_eve:
                    fest_eves.append(d_str)

            return fest_names, fest_mults, fest_eves
        except Exception as e:
            print(f"⚠️ Error loading festivals.csv: {e}")

    fallback_names = {
        "01-01": "New Year Day", "01-14": "Makar Sankranti", "01-15": "Makar Sankranti", "01-26": "Republic Day", "03-25": "Holi",
        "08-15": "Independence Day", "09-07": "Ganesh Chaturthi", "10-02": "Gandhi Jayanti",
        "10-12": "Dussehra", "11-01": "Diwali", "11-02": "Diwali Balipratipada",
        "12-25": "Christmas", "12-31": "New Year Eve"
    }

    fallback_eves = ["12-30", "12-31", "10-31", "10-11", "08-14", "12-24"]
    return fallback_names, {}, fallback_eves

FESTIVALS, FESTIVAL_MULTS, FESTIVAL_EVES = load_festivals_dict()

def safe_int(val: Any, default: int = 0) -> int:
    if val is None or pd.isna(val):
        return default
    if isinstance(val, (pd.Timestamp, datetime, date)):
        return default
    try:
        return int(float(val))
    except Exception:
        return default

def safe_float(val: Any, default: float = 0.0) -> float:
    if val is None or pd.isna(val):
        return default
    if isinstance(val, (pd.Timestamp, datetime, date)):
        return default
    try:
        return float(val)
    except Exception:
        return default

class BusinessInsightDiscoverer:
    @classmethod
    def discover_and_save_insights(cls, df: pd.DataFrame):
        """
        Phase 5: Automatically discover business insights from historical bookings
        and save them to be used as engineered features.
        """
        try:
            df = df.copy()
            if "booking_date" in df.columns:
                df["dt"] = pd.to_datetime(df["booking_date"], errors="coerce")
                df["m"] = df["dt"].dt.month
                df["wday"] = df["dt"].dt.weekday
            else:
                df["m"] = 7
                df["wday"] = 5
                
            p_col = "selling_price" if "selling_price" in df.columns else "price"
            df[p_col] = pd.to_numeric(df[p_col], errors="coerce").fillna(0.0)
            
            # 1. Highest revenue weekday and month
            revenue_by_wday = df.groupby("wday")[p_col].sum()
            highest_revenue_weekday = int(revenue_by_wday.idxmax()) if not revenue_by_wday.empty else 6
            
            revenue_by_month = df.groupby("m")[p_col].sum()
            highest_revenue_month = int(revenue_by_month.idxmax()) if not revenue_by_month.empty else 5
            
            # 2. Most and least booked slot
            slot_counts = df["commercial_slot"].value_counts() if "commercial_slot" in df.columns else pd.Series()
            most_booked_slot = str(slot_counts.idxmax()) if not slot_counts.empty else "12H_DAY"
            least_booked_slot = str(slot_counts.idxmin()) if not slot_counts.empty else "COUPLE_NIGHT"
            
            # 3. Weekend premium ratio
            wk_prices = df[df["is_weekend"] == 1][p_col] if "is_weekend" in df.columns else pd.Series()
            wd_prices = df[df["is_weekend"] == 0][p_col] if "is_weekend" in df.columns else pd.Series()
            wk_avg = wk_prices.mean() if not wk_prices.empty else 4000.0
            wd_avg = wd_prices.mean() if not wd_prices.empty else 3000.0
            weekend_premium_ratio = round(float(wk_avg / wd_avg), 3) if wd_avg > 0 else 1.25
            
            # 4. Summer and winter demand ratio vs monsoon
            ms_prices = df[df["month"].isin([6, 7, 8, 9])][p_col] if "month" in df.columns else pd.Series()
            sm_prices = df[df["month"].isin([3, 4, 5])][p_col] if "month" in df.columns else pd.Series()
            wt_prices = df[df["month"].isin([10, 11, 12, 1, 2])][p_col] if "month" in df.columns else pd.Series()
            ms_avg = ms_prices.mean() if not ms_prices.empty else 3000.0
            sm_avg = sm_prices.mean() if not sm_prices.empty else 3600.0
            wt_avg = wt_prices.mean() if not wt_prices.empty else 3200.0
            
            summer_demand_ratio = round(float(sm_avg / ms_avg), 3) if ms_avg > 0 else 1.20
            winter_demand_ratio = round(float(wt_avg / ms_avg), 3) if ms_avg > 0 else 1.05
            
            # 5. Rain impact ratio
            rainy_prices = df[df["rain_probability"] > 50.0][p_col] if "rain_probability" in df.columns else pd.Series()
            sunny_prices = df[df["rain_probability"] <= 50.0][p_col] if "rain_probability" in df.columns else pd.Series()
            rainy_avg = rainy_prices.mean() if not rainy_prices.empty else 2800.0
            sunny_avg = sunny_prices.mean() if not sunny_prices.empty else 3500.0
            rain_impact_ratio = round(float(rainy_avg / sunny_avg), 3) if sunny_avg > 0 else 0.85
            
            # 6. Lead time effect
            adv_prices = df[df["lead_days"] > 14][p_col] if "lead_days" in df.columns else pd.Series()
            last_prices = df[df["lead_days"] <= 14][p_col] if "lead_days" in df.columns else pd.Series()
            adv_avg = adv_prices.mean() if not adv_prices.empty else 3800.0
            last_avg = last_prices.mean() if not last_prices.empty else 3400.0
            advance_booking_ratio = round(float(adv_avg / last_avg), 3) if last_avg > 0 else 1.10
            
            # 7. Occupancy ratio
            occupancy = 0.65
            if "occupancy_ratio" in df.columns:
                occupancy = df["occupancy_ratio"].mean()
            elif "occupancy_rate" in df.columns:
                occupancy = df["occupancy_rate"].mean()
            
            insights = {
                "highest_revenue_weekday": highest_revenue_weekday,
                "highest_revenue_month": highest_revenue_month,
                "most_booked_slot": most_booked_slot,
                "least_booked_slot": least_booked_slot,
                "weekend_premium_ratio": weekend_premium_ratio,
                "summer_demand_ratio": summer_demand_ratio,
                "winter_demand_ratio": winter_demand_ratio,
                "rain_impact_ratio": rain_impact_ratio,
                "advance_booking_ratio": advance_booking_ratio,
                "average_occupancy": round(float(occupancy), 3)
            }
            
            insights_path = DATA_DIR / "business_insights.json"
            with open(insights_path, "w") as f:
                json.dump(insights, f, indent=2)
            print(f"📊 [INSIGHT DISCOVERY] Automatically discovered and saved business insights: {list(insights.keys())}")
            
            # Force reload in FeatureEngineer cache
            FeatureEngineer._insights = insights
            cls.discover_festival_intelligence(df)
        except Exception as ex:
            print(f"⚠️ Error discovering business insights: {ex}")

    @classmethod
    def discover_festival_intelligence(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Learns festival intelligence per festival name strictly from historical records in Farm_Booking_Data.xlsx.
        """
        try:
            df = df.copy()
            p_col = "selling_price" if "selling_price" in df.columns else "price"
            df[p_col] = pd.to_numeric(df[p_col], errors="coerce").fillna(0.0)
            
            fest_profile = {}
            if "festival_name" in df.columns or "is_festival" in df.columns:
                df_valid = df[df[p_col] > 0]
                non_fest_rows = df_valid[df_valid.get("is_festival", 0) == 0]
                non_fest_mean = float(non_fest_rows[p_col].mean()) if len(non_fest_rows) > 0 else 4000.0
                
                fest_mask = df_valid["festival_name"].notna() & (df_valid["festival_name"].astype(str).str.strip() != "") & (df_valid["festival_name"].astype(str).str.strip() != "No Festival")
                fest_rows = df_valid[fest_mask]
                
                for f_name, group in fest_rows.groupby("festival_name"):
                    count = len(group)
                    avg_p = float(group[p_col].mean())
                    med_p = float(group[p_col].median())
                    std_p = float(group[p_col].std()) if count > 1 else 0.0
                    
                    prem_avg = round(avg_p / non_fest_mean, 3) if non_fest_mean > 0 else 1.0
                    prem_med = round(med_p / non_fest_mean, 3) if non_fest_mean > 0 else 1.0
                    confidence = round(min(1.0, count / 5.0), 2)
                    
                    wk_group = group[group["is_weekend"] == 1] if "is_weekend" in group.columns else pd.DataFrame()
                    wd_group = group[group["is_weekend"] == 0] if "is_weekend" in group.columns else pd.DataFrame()
                    
                    wk_interaction = 1.0
                    if len(wk_group) > 0 and len(wd_group) > 0 and wd_group[p_col].mean() > 0:
                        wk_interaction = round(float(wk_group[p_col].mean() / wd_group[p_col].mean()), 3)
                        
                    dur_mean = float(group["duration_hours"].mean()) if "duration_hours" in group.columns else 24.0
                    
                    fest_profile[str(f_name)] = {
                        "historical_sample_count": count,
                        "average_price": round(avg_p, 2),
                        "median_price": round(med_p, 2),
                        "std_price": round(std_p, 2),
                        "average_premium": prem_avg,
                        "median_premium": prem_med,
                        "confidence_score": confidence,
                        "peak_duration": round(dur_mean, 1),
                        "weekend_interaction": wk_interaction
                    }
                    
            fest_path = DATA_DIR / "learned_festival_intelligence.json"
            with open(fest_path, "w") as f:
                json.dump(fest_profile, f, indent=2)
            print(f"🎉 [FESTIVAL INTELLIGENCE] Discovered intelligence for {len(fest_profile)} festivals.")
            return fest_profile
        except Exception as ex:
            print(f"⚠️ Error discovering festival intelligence: {ex}")
            return {}


class FeatureEngineer:
    _insights = None
    _group_averages_cache = None
    _weekend_intelligence = None

    @classmethod
    def purge_cache(cls):
        cls._group_averages_cache = None
        cls._weekend_intelligence = None

    @classmethod
    def get_group_averages(cls) -> Dict[str, Any]:
        if cls._group_averages_cache is None:
            import json
            avg_path = DATA_DIR / "group_averages.json"
            if avg_path.exists():
                try:
                    with open(avg_path, "r") as f:
                        cls._group_averages_cache = json.load(f)
                except Exception:
                    cls._group_averages_cache = {}
            else:
                cls._group_averages_cache = {}
        return cls._group_averages_cache

    @classmethod
    def _load_insights(cls) -> Dict[str, Any]:
        if cls._insights is not None:
            return cls._insights
        
        insights_path = DATA_DIR / "business_insights.json"
        if insights_path.exists():
            try:
                with open(insights_path, "r") as f:
                    cls._insights = json.load(f)
                    return cls._insights
            except Exception:
                pass
                
        # Default fallback values if no file exists
        cls._insights = {
            "highest_revenue_month": 5,
            "highest_revenue_weekday": 6,
            "weekend_premium_ratio": 1.25,
            "summer_demand_ratio": 1.2,
            "winter_demand_ratio": 1.0,
            "rain_impact_ratio": 0.85,
            "advance_booking_ratio": 1.1,
            "average_occupancy": 0.65
        }
        return cls._insights

    @classmethod
    def _load_weekend_intelligence(cls) -> Dict[str, int]:
        if cls._weekend_intelligence is not None:
            return cls._weekend_intelligence
            
        wknd_path = DATA_DIR / "learned_weekend_intelligence.json"
        if wknd_path.exists():
            try:
                import json
                with open(wknd_path, "r") as f:
                    cls._weekend_intelligence = json.load(f)
                    return cls._weekend_intelligence
            except Exception:
                pass
                
        cls._weekend_intelligence = {}
        return cls._weekend_intelligence

    @classmethod
    def discover_weekend_intelligence(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Learns from historical data which combinations of (day_of_week, commercial_slot)
        are officially treated as weekends by the business.
        """
        try:
            df = df.copy()
            if "booking_date" in df.columns and "day_of_week" not in df.columns:
                df["booking_date_dt"] = pd.to_datetime(df["booking_date"], errors="coerce")
                df["day_of_week"] = df["booking_date_dt"].dt.weekday
                
            if "is_weekend" not in df.columns or "day_of_week" not in df.columns or "commercial_slot" not in df.columns:
                return {}
            
            weekend_profile = {}
            # Group by day_of_week and commercial_slot
            grouped = df.groupby(["day_of_week", "commercial_slot"])["is_weekend"].mean().reset_index()
            
            for _, row in grouped.iterrows():
                dow = int(row["day_of_week"])
                slot = str(row["commercial_slot"])
                # If it's historically marked as weekend > 50% of the time, treat it as weekend
                is_wknd = 1 if float(row["is_weekend"]) > 0.5 else 0
                
                key = f"{dow}_{slot}"
                weekend_profile[key] = is_wknd
                
            wknd_path = DATA_DIR / "learned_weekend_intelligence.json"
            with open(wknd_path, "w") as f:
                json.dump(weekend_profile, f, indent=2)
                
            print(f"🎉 [WEEKEND INTELLIGENCE] Discovered {sum(weekend_profile.values())} official weekend slots out of {len(weekend_profile)} combinations.")
            return weekend_profile
        except Exception as ex:
            print(f"⚠️ Error discovering weekend intelligence: {ex}")
            return {}

    @classmethod
    def compute_advanced_time_series_features(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["booking_date_dt"] = pd.to_datetime(df["booking_date"])
        df.sort_values(by="booking_date_dt", ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        # Initialize lag columns with fallback values
        df["slot_lag_price_1"] = 8500.0
        df["slot_lag_price_2"] = 8500.0
        
        # Compute slot-specific lags
        for slot in df["commercial_slot"].unique():
            slot_mask = df["commercial_slot"] == slot
            slot_prices = df.loc[slot_mask, "selling_price"]
            df.loc[slot_mask, "slot_lag_price_1"] = slot_prices.shift(1).fillna(8500.0)
            df.loc[slot_mask, "slot_lag_price_2"] = slot_prices.shift(2).fillna(8500.0)
            
        # Days since last booking
        df["days_since_last_booking"] = df["booking_date_dt"].diff().dt.days.fillna(0.0).astype(float)
        
        # Rolling price averages within the same slot
        df["rolling_price_mean_30"] = 8500.0
        for slot in df["commercial_slot"].unique():
            slot_mask = df["commercial_slot"] == slot
            df.loc[slot_mask, "rolling_price_mean_30"] = df.loc[slot_mask, "selling_price"].rolling(window=10, min_periods=1).mean().fillna(8500.0)
            
        # Rolling demand & bookings count (Historical Demand)
        df_temp = df.set_index("booking_date_dt")
        df["bookings_last_7d"] = df_temp.rolling("7D")["selling_price"].count().values.astype(float)
        df["bookings_last_30d"] = df_temp.rolling("30D")["selling_price"].count().values.astype(float)
        
        # Occupancy features (rolling occupancy estimation)
        df["occupancy_rate_7d"] = (df["bookings_last_7d"] / 7.0).clip(0.0, 1.0)
        df["occupancy_rate_30d"] = (df["bookings_last_30d"] / 30.0).clip(0.0, 1.0)
        
        # Booking velocity
        df["booking_velocity"] = (df["bookings_last_7d"] / 7.0).astype(float)
        
        # V2 Occupancy Intelligence
        df["month_year"] = df["booking_date_dt"].dt.to_period("M")
        month_counts = df.groupby("month_year")["selling_price"].transform("count").astype(float)
        df["current_occupancy_pct"] = (month_counts / 120.0).clip(0.0, 1.0)
        df["remaining_inventory"] = (120.0 - month_counts).clip(lower=0.0)
        df["booking_pace"] = (df["bookings_last_7d"] / 7.0) / (df["bookings_last_30d"] / 30.0 + 1e-5)
        df["booking_pace"] = df["booking_pace"].clip(0.1, 5.0).fillna(1.0)
        df["occupancy_trend"] = df["occupancy_rate_7d"] - df["occupancy_rate_30d"]
        
        if "month_year" in df.columns:
            df.drop(columns=["month_year"], inplace=True)
            
        return df

    @classmethod
    def calculate_group_averages(cls, df: pd.DataFrame):
        cls.purge_cache()
        cls.discover_weekend_intelligence(df)
        try:
            avg_dict = {}
            
            # Ensure month, year, is_weekend, selling_price, person_count are numeric and slot normalized
            df = df.copy()
            
            df["commercial_slot"] = df["commercial_slot"].apply(lambda s: slot_engine.normalize_commercial_slot(s))
            if "booking_date" in df.columns:
                dt_s = pd.to_datetime(df["booking_date"], errors="coerce")
                df["month"] = dt_s.dt.month.fillna(6).astype(int)
                df["year"] = dt_s.dt.year.fillna(2026).astype(int)
                df["is_weekend"] = dt_s.dt.weekday.isin([4, 5, 6]).astype(int) # Include Friday as weekend for farmhouses
            else:
                if "month" not in df.columns: df["month"] = 6
                else: df["month"] = pd.to_numeric(df["month"], errors="coerce").fillna(6).astype(int)
                
                if "year" not in df.columns: df["year"] = 2026
                else: df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(2026).astype(int)
                
                if "is_weekend" not in df.columns: df["is_weekend"] = 0
                else: df["is_weekend"] = pd.to_numeric(df["is_weekend"], errors="coerce").fillna(0).astype(int)

            if "is_festival" not in df.columns: df["is_festival"] = 0
            else: df["is_festival"] = pd.to_numeric(df["is_festival"], errors="coerce").fillna(0).astype(int)

            if "festival_name" not in df.columns: df["festival_name"] = ""

            if "person_count" not in df.columns: df["person_count"] = 4
            else: df["person_count"] = pd.to_numeric(df["person_count"], errors="coerce").fillna(4).astype(int)


            
            # Normalize selling price based on domain duration rules (6-12h anchored to 12H, 13-25h anchored to 24H)
            if "duration_hours" not in df.columns: df["duration_hours"] = 24.0
            else: df["duration_hours"] = pd.to_numeric(df["duration_hours"], errors="coerce").fillna(24.0)
            
            def calc_norm_price(row_p, row_d):
                p = float(row_p)
                d = float(row_d)
                if 6 <= d <= 12:
                    return p  # 12-hour base equivalent (hourly = p / 12.0)
                elif 13 <= d <= 25:
                    return p  # 24-hour base equivalent (hourly = p / 24.0)
                else:
                    daily_factor = max(1.0, d / 24.0)
                    return p / daily_factor

            df["norm_selling_price"] = df.apply(lambda r: calc_norm_price(r["selling_price"], r["duration_hours"]), axis=1)
            
            # Dynamic Marginal Guest Cost Calculation (Covariance / Variance slope) with Regularization
            def compute_slope(df_sub):
                if len(df_sub) > 5 and df_sub["person_count"].nunique() > 1:
                    # Use all records (including top 10% VIP prices) as requested
                    df_clean = df_sub.copy()
                    
                    if len(df_clean) > 5 and df_clean["person_count"].nunique() > 1:
                        cov = df_clean["norm_selling_price"].cov(df_clean["person_count"])
                        var = df_clean["person_count"].var()
                        if var > 0:
                            raw_slope = float(cov / var)
                            # Regularize slope: Floor at 30, Cap at 100 to prevent runaway pricing
                            return min(100.0, max(30.0, raw_slope))
                return 50.0  # Fallback if insufficient variance
            
            global_marginal_cost = compute_slope(df)
            avg_dict["marginal_guest_cost_global"] = global_marginal_cost
            
            slot_cost_map = {}
            for slot in df["commercial_slot"].unique():
                slot_cost = compute_slope(df[df["commercial_slot"] == slot])
                slot_norm = slot_engine.normalize_commercial_slot(slot)
                avg_dict[f"marginal_guest_cost_{slot_norm}"] = slot_cost
                slot_cost_map[slot] = slot_cost
                
            df["marginal_cost"] = df["commercial_slot"].map(slot_cost_map).fillna(global_marginal_cost)
            
            df["extra_guests"] = df["person_count"].apply(lambda p: max(0, int(p) - 4))
            df["base_selling_price"] = df["norm_selling_price"] - df["extra_guests"] * df["marginal_cost"]


            # --- FESTIVAL EXCLUSION LOGIC ---
            # Save the full dataset (with base_selling_price) for features that explicitly group by is_festival
            df_full = df.copy()
            # Do not consider ANY festival record for calculating general averages to avoid skewing normal prices
            df = df[df["is_festival"] == 0]


            # 1. slot_month_weekend_avg & independent segment statistics (using base_selling_price)
            gp1 = df.groupby(["commercial_slot", "month", "is_weekend"])["base_selling_price"].mean().reset_index()
            for _, row in gp1.iterrows():
                key = f"slot_month_weekend_{row['commercial_slot']}_{int(row['month'])}_{int(row['is_weekend'])}"
                avg_dict[key] = float(row["base_selling_price"])
            
            # Month & Slot Specific Weekend Premium Ratios
            gp_wk = df[df["is_weekend"] == 1].groupby(["commercial_slot", "month"])["base_selling_price"].mean().reset_index()
            gp_wd = df[df["is_weekend"] == 0].groupby(["commercial_slot", "month"])["base_selling_price"].mean().reset_index()
            wd_map = {(row['commercial_slot'], int(row['month'])): float(row['base_selling_price']) for _, row in gp_wd.iterrows()}

            
            for _, row in gp_wk.iterrows():
                slot_code = str(row['commercial_slot'])
                slot_norm = slot_engine.normalize_commercial_slot(slot_code)
                m_code = int(row['month'])
                wk_mean = float(row['base_selling_price'])
                wd_mean = wd_map.get((slot_code, m_code), 0.0)
                
                # Absolute rupee difference calculation (No percentage multiplication!)
                abs_diff = round(wk_mean - wd_mean, 2) if wd_mean > 0 else 0.0
                ratio = round(wk_mean / wd_mean, 3) if wd_mean > 0 else 1.25
                
                for s_key in set([slot_code, slot_norm]):
                    key_diff = f"slot_month_weekend_diff_{s_key}_{m_code}"
                    avg_dict[key_diff] = abs_diff
                    key = f"slot_month_weekend_ratio_{s_key}_{m_code}"
                    avg_dict[key] = ratio

            # Learned Commercial Ratio Engine (24H vs 12H)
            gp_slot = df_full.groupby(["month", "is_weekend", "is_festival", "commercial_slot"])["base_selling_price"].median().reset_index()
            # We need to map 24H -> 12H equivalents
            for (m_c, w_c, f_c), group in gp_slot.groupby(["month", "is_weekend", "is_festival"]):
                prices = {row["commercial_slot"]: row["base_selling_price"] for _, row in group.iterrows()}
                
                # Check pairs (e.g. 24H Day -> 12H Day, 24H Night -> 12H Night)
                for c_slot, c_price in prices.items():
                    if "24H" in c_slot:
                        eq_12h = c_slot.replace("24H", "12H")
                        if eq_12h in prices and prices[eq_12h] > 0:
                            ratio = round(c_price / prices[eq_12h], 3)
                            avg_dict[f"learned_ratio_24_12_{c_slot}_{int(m_c)}_{int(w_c)}_{int(f_c)}"] = ratio


            # Independent Segment Statistics (mean, median, std, count, confidence, p25, p75)
            gp_stats = df.groupby(["commercial_slot", "month", "is_weekend"])["base_selling_price"].agg(
                mean="mean",
                median="median",
                std="std",
                count="count",
                p25=lambda x: np.percentile(x, 25),
                p75=lambda x: np.percentile(x, 75)
            ).reset_index()
            
            for _, row in gp_stats.iterrows():
                slot_c = str(row["commercial_slot"])
                slot_norm = slot_engine.normalize_commercial_slot(slot_c)
                m_c = int(row["month"])
                w_c = int(row["is_weekend"])
                cnt = int(row["count"])
                
                for s_key in set([slot_c, slot_norm]):
                    prefix = f"seg_{s_key}_{m_c}_{w_c}"
                    avg_dict[f"{prefix}_mean"] = float(row["mean"])
                    avg_dict[f"{prefix}_median"] = float(row["median"])
                    avg_dict[f"{prefix}_std"] = float(row["std"]) if pd.notna(row["std"]) else 0.0
                    avg_dict[f"{prefix}_count"] = float(cnt)
                    avg_dict[f"{prefix}_confidence"] = float(min(1.0, cnt / 5.0))
                    avg_dict[f"{prefix}_p25"] = float(row["p25"])
                    avg_dict[f"{prefix}_p75"] = float(row["p75"])

            # Trimmed Mean & Weighted Median for outlier resistance
            for (slot_c, m_c, w_c), grp in df.groupby(["commercial_slot", "month", "is_weekend"]):
                slot_norm = slot_engine.normalize_commercial_slot(slot_c)
                prices = grp["base_selling_price"].sort_values().values

                # Use standard mean instead of trimmed mean to include all top 10% data
                t_mean = float(np.mean(prices))
                    
                w_med = float(np.median(prices))
                for s_key in set([str(slot_c), slot_norm]):
                    prefix = f"seg_{s_key}_{int(m_c)}_{int(w_c)}"
                    avg_dict[f"{prefix}_trimmed_mean"] = t_mean
                    avg_dict[f"{prefix}_weighted_median"] = w_med



                
            # 2. slot_weekend_avg
            gp2 = df.groupby(["commercial_slot", "is_weekend"])["selling_price"].mean().reset_index()
            for _, row in gp2.iterrows():
                key = f"slot_weekend_{row['commercial_slot']}_{int(row['is_weekend'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 3. slot_festival_avg
            gp3 = df_full.groupby(["commercial_slot", "is_festival"])["selling_price"].mean().reset_index()
            for _, row in gp3.iterrows():
                key = f"slot_festival_{row['commercial_slot']}_{int(row['is_festival'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 4. slot_person_avg
            gp4 = df.groupby(["commercial_slot", "person_count"])["selling_price"].mean().reset_index()
            for _, row in gp4.iterrows():
                key = f"slot_person_{row['commercial_slot']}_{int(row['person_count'])}"
                avg_dict[key] = float(row["selling_price"])

            # 5. slot_month_avg
            gp5 = df.groupby(["commercial_slot", "month"])["selling_price"].mean().reset_index()
            for _, row in gp5.iterrows():
                key = f"slot_month_{row['commercial_slot']}_{int(row['month'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 6. slot_month_weekday_avg (where is_weekend == 0)
            gp6 = df[df["is_weekend"] == 0].groupby(["commercial_slot", "month"])["selling_price"].mean().reset_index()
            for _, row in gp6.iterrows():
                key = f"slot_month_weekday_{row['commercial_slot']}_{int(row['month'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 7. slot_person_month_avg
            gp7 = df.groupby(["commercial_slot", "person_count", "month"])["selling_price"].mean().reset_index()
            for _, row in gp7.iterrows():
                key = f"slot_person_month_{row['commercial_slot']}_{int(row['person_count'])}_{int(row['month'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 8. slot_person_weekend_avg
            gp8 = df.groupby(["commercial_slot", "person_count", "is_weekend"])["selling_price"].mean().reset_index()
            for _, row in gp8.iterrows():
                key = f"slot_person_weekend_{row['commercial_slot']}_{int(row['person_count'])}_{int(row['is_weekend'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 9. month_slot_booking_count
            gp9 = df.groupby(["month", "commercial_slot"])["selling_price"].count().reset_index()
            for _, row in gp9.iterrows():
                key = f"month_slot_booking_count_{int(row['month'])}_{row['commercial_slot']}"
                avg_dict[key] = float(row["selling_price"])
                
            # 10. month_slot_avg_price
            gp10 = df.groupby(["month", "commercial_slot"])["selling_price"].mean().reset_index()
            for _, row in gp10.iterrows():
                key = f"month_slot_avg_price_{int(row['month'])}_{row['commercial_slot']}"
                avg_dict[key] = float(row["selling_price"])
                
            # 11. month_weekend_demand
            gp11 = df[df["is_weekend"] == 1].groupby(["month"])["selling_price"].count().reset_index()
            for _, row in gp11.iterrows():
                key = f"month_weekend_demand_{int(row['month'])}"
                avg_dict[key] = float(row["selling_price"])
                
            # 12. previous_year_same_month_slot_avg
            gp12 = df.groupby(["year", "month", "commercial_slot"])["selling_price"].mean().reset_index()
            for _, row in gp12.iterrows():
                key = f"year_month_slot_{int(row['year'])}_{int(row['month'])}_{row['commercial_slot']}"
                avg_dict[key] = float(row["selling_price"])
                
            # Slot overall fallback
            gp_slot = df.groupby(["commercial_slot"])["selling_price"].mean().reset_index()
            for _, row in gp_slot.iterrows():
                key = f"slot_overall_{row['commercial_slot']}"
                avg_dict[key] = float(row["selling_price"])
                
            avg_path = DATA_DIR / "group_averages.json"
            with open(avg_path, "w") as f:
                json.dump(avg_dict, f, indent=2)
            print(f"📊 [FEATURE ENGINEERING] Saved {len(avg_dict)} group averages to group_averages.json")
            return avg_dict
        except Exception as e:
            print(f"⚠️ Error saving group averages: {e}")
            return {}

    @classmethod
    def extract_features_from_dict(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts engineered feature dictionary for a single booking request or record.
        Includes Couple Discount (2 guests consume less electricity/water) & auto lead days calculation.
        """
        raw_date = row.get("booking_date")
        today_date = date.today()

        if isinstance(raw_date, (pd.Timestamp, datetime)):
            dt = raw_date
        elif isinstance(raw_date, date):
            dt = datetime.combine(raw_date, datetime.min.time())
        elif raw_date:
            date_str = str(raw_date).split()[0]
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except Exception:
                try:
                    dt = pd.to_datetime(raw_date).to_pydatetime()
                except Exception:
                    dt = datetime.now()
        else:
            dt = datetime.combine(today_date, datetime.min.time())

        target_date = dt.date()
        month = int(dt.month)
        import math
        month_rad = 2.0 * math.pi * month / 12.0
        month_sin = math.sin(month_rad)
        month_cos = math.cos(month_rad)
        year = int(dt.year)
        day_of_week = int(dt.weekday()) # 0 = Monday, 6 = Sunday
        
        # New Commercial Weekend Rule (Dynamic Intelligence)
        commercial_slot = row.get("commercial_slot", str(row.get("slot_type", "")))
        commercial_slot = slot_engine.normalize_commercial_slot(commercial_slot).strip().title()
        
        # 1. Trust explicit 'is_weekend' if provided in the row (e.g. historical data processing)
        if "is_weekend" in row and pd.notna(row["is_weekend"]):
            is_weekend = int(float(row["is_weekend"]))
        else:
            is_weekend = 0
            if day_of_week == 5 and "Night" in commercial_slot and start_dt.hour >= 17:
                is_weekend = 1
            elif day_of_week == 6 and "Day" in commercial_slot and 6 <= start_dt.hour <= 12:
                is_weekend = 1

        # Intelligent Festival Demand Window Engine
        from app.services.festival_engine import festival_engine
        
        if "is_festival" in row and pd.notna(row["is_festival"]):
            is_festival = int(float(row["is_festival"]))
            festival_name = row.get("festival_name", "Festival")
            is_festival_eve = int(float(row.get("is_festival_eve", 0)))
            days_before_festival = int(float(row.get("days_before_festival", 7)))
            days_after_festival = int(float(row.get("days_after_festival", 7)))
            festival_features = {
                "festival_detected": bool(is_festival),
                "festival_name": festival_name,
                "festival_category": "Standard",
                "festival_tier": "Tier 2",
                "festival_demand_level": "High",
                "festival_multiplier": 1.0,
                "festival_overlap_hours": 0.0,
                "festival_overlap_percentage": 0.0,
                "festival_window_start": None,
                "festival_window_end": None,
                "days_before_festival": days_before_festival,
                "days_after_festival": days_after_festival,
                "is_peak_festival": False,
                "multiple_festival_overlap": False,
                "highest_priority_festival": festival_name,
                "is_festival": is_festival
            }
        else:
            duration_hours = float(row.get("duration_hours", 24.0))
            if 'Night' in commercial_slot:
                start_hour = 18
            else:
                start_hour = 8
                
            check_in = dt.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            check_out = check_in + pd.Timedelta(hours=duration_hours)
            
            festival_features = festival_engine.detect_festivals(check_in, check_out)
            
            is_festival = festival_features["is_festival"]
            festival_name = festival_features["festival_name"]
            is_festival_eve = 1 if festival_features["days_before_festival"] == 1 else 0
            days_before_festival = festival_features["days_before_festival"]
            days_after_festival = festival_features["days_after_festival"]

        if "is_vacation" in row and pd.notna(row["is_vacation"]):
            is_vacation = int(float(row["is_vacation"]))
        else:
            is_vacation = 1 if month in [5, 12, 1] else 0

        # Season
        if "season" in row and pd.notna(row["season"]):
            season = str(row["season"]).strip().title()
            season_monsoon = 1 if season == "Monsoon" else 0
            season_summer = 1 if season == "Summer" else 0
            season_winter = 1 if season == "Winter" else 0
        else:
            if month in [6, 7, 8, 9]:
                season = "Monsoon"
                season_monsoon = 1
                season_summer = 0
                season_winter = 0
            elif month in [3, 4, 5]:
                season = "Summer"
                season_monsoon = 0
                season_summer = 1
                season_winter = 0
            else:
                season = "Winter"
                season_monsoon = 0
                season_summer = 0
                season_winter = 1

        # Summer (Mar-May) is Peak Season; Winter (Nov-Feb) is Off-Season
        is_peak_season = 1 if (is_weekend or is_festival or is_vacation or month in [3, 4, 5]) else 0
        is_off_season = 1 if (month in [11, 12, 1, 2] and not is_weekend and not is_festival) else 0

        person_count = safe_int(row.get("person_count"), 4)
        
        # Couple Designation Logic (Step 3 Rule)
        is_couple = 1 if person_count == 2 else 0
        is_family = 1 if 3 <= person_count <= 12 else 0
        is_corporate = 1 if person_count > 12 else 0

        slot_type = slot_engine.normalize_commercial_slot(row.get("slot_type", row.get("commercial_slot", "12H Day")))
        commercial_slot = slot_type # backwards compatibility
        
        passed_lead_days = row.get("lead_days")
        if passed_lead_days is not None and safe_int(passed_lead_days, -1) >= 0:
            lead_days = safe_int(passed_lead_days, 0)
        else:
            lead_days = max(0, (target_date - today_date).days)
        
        if lead_days == 0:
            lead_time_cat = "Same Day"
        elif lead_days <= 3:
            lead_time_cat = "Last Minute"
        elif lead_days <= 14:
            lead_time_cat = "Standard"
        elif lead_days <= 30:
            lead_time_cat = "Advance"
        else:
            lead_time_cat = "Far Advance"

        is_long_weekend = 1 if (is_weekend and (is_festival or is_festival_eve or is_vacation or days_before_festival <= 1 or days_after_festival <= 1)) else 0
        is_consecutive_holiday = 1 if (is_festival or is_festival_eve or days_before_festival == 1 or days_after_festival == 1) else 0
        is_school_vacation = 1 if month in [5, 10, 12] else 0
        is_local_vacation = 1 if month in [5, 10, 12, 1] else 0
        
        try:
            week_of_year = int(dt.isocalendar().week)
            day_of_year = int(dt.timetuple().tm_yday)
        except Exception:
            week_of_year = 1
            day_of_year = 1

        if lead_days <= 2:
            lead_time_bucket = 0  # 0-2 days (Last Minute)
        elif lead_days <= 7:
            lead_time_bucket = 1  # 3-7 days (Standard)
        elif lead_days <= 30:
            lead_time_bucket = 2  # 8-30 days (Advance)
        else:
            lead_time_bucket = 3  # 30+ days (Far Advance)

        competitor_price = safe_float(row.get("competitor_price"), 0.0)
        
        temp = safe_float(row.get("temperature"), 26.0)
        rain_prob = safe_float(row.get("rain_probability"), 20.0)
        humidity = safe_float(row.get("humidity"), 60.0)
        wind_speed = safe_float(row.get("wind_speed"), 4.2)
        cloud_cover = safe_float(row.get("cloud_cover"), 25.0)

        # Dynamic Demand & Insights engineering (Phase 5 & 6)
        insights = cls._load_insights()
        weekend_premium = insights.get("weekend_premium_ratio", 1.25)
        summer_demand_ratio = insights.get("summer_demand_ratio", 1.2)
        winter_demand_ratio = insights.get("winter_demand_ratio", 1.0)
        rain_impact_ratio = insights.get("rain_impact_ratio", 0.85)

        base_demand = 50.0
        if is_weekend:
            base_demand *= weekend_premium
        if season == "Summer":
            base_demand *= summer_demand_ratio
        elif season == "Winter":
            base_demand *= winter_demand_ratio
        if temp > 33.0 or rain_prob > 50.0:
            base_demand *= rain_impact_ratio
            
        demand_score = min(100.0, max(10.0, base_demand))

        # Business Confidence Score
        business_confidence_score = 90.0
        if lead_days > 14:
            business_confidence_score = 95.0
        elif lead_days < 2:
            business_confidence_score = 75.0
        
        # Historical group averages lookups (Phase 8 & 9)
        avg_dict = cls.get_group_averages()
        slot_month_weekend_ratio = avg_dict.get(f"slot_month_weekend_ratio_{slot_type}_{month}", 1.25)
        slot_month_weekend_diff = avg_dict.get(f"slot_month_weekend_diff_{slot_type}_{month}", 0.0)
        
        prefix = f"seg_{slot_type}_{month}_{is_weekend}"

        segment_mean = avg_dict.get(f"{prefix}_mean", 8500.0)
        segment_median = avg_dict.get(f"{prefix}_median", 8500.0)
        segment_trimmed_mean = avg_dict.get(f"{prefix}_trimmed_mean", segment_mean)
        segment_weighted_median = avg_dict.get(f"{prefix}_weighted_median", segment_median)
        segment_std = avg_dict.get(f"{prefix}_std", 0.0)
        segment_count = avg_dict.get(f"{prefix}_count", 0.0)
        segment_confidence = avg_dict.get(f"{prefix}_confidence", 0.5)
        p25_price = avg_dict.get(f"{prefix}_p25", 8500.0 * 0.85)
        p75_price = avg_dict.get(f"{prefix}_p75", 8500.0 * 1.15)


        slot_month_weekend_avg = avg_dict.get(f"slot_month_weekend_{slot_type}_{month}_{is_weekend}", segment_mean)
        slot_weekend_avg = avg_dict.get(f"slot_weekend_{slot_type}_{is_weekend}", segment_mean)
        slot_festival_avg = avg_dict.get(f"slot_festival_{slot_type}_{is_festival}", segment_mean)
        slot_person_avg = avg_dict.get(f"slot_person_{slot_type}_{person_count}", segment_mean)
        
        slot_month_avg = avg_dict.get(f"slot_month_{slot_type}_{month}", segment_mean)
        slot_month_weekday_avg = avg_dict.get(f"slot_month_weekday_{slot_type}_{month}", segment_mean)
        slot_person_month_avg = avg_dict.get(f"slot_person_month_{slot_type}_{person_count}_{month}", segment_mean)
        month_slot_avg = avg_dict.get(f"month_slot_avg_price_{month}_{slot_type}", segment_mean)
        month_weekend_slot_avg = slot_month_weekend_avg
        month_guest_slot_avg = slot_person_month_avg
        month_festival_slot_avg = slot_festival_avg
        month_leadtime_slot_avg = segment_mean
        month_weather_slot_avg = segment_mean
        hierarchical_fallback_avg = segment_mean
        hierarchical_confidence_score = segment_confidence
        hierarchical_matched_level = 1 if segment_count >= 3 else 3


        slot_capacity_hours = 24.0 if "24H" in slot_type.upper() else 12.0
        duration_hours = safe_float(row.get("duration_hours"), slot_capacity_hours)
        if duration_hours <= 0:
            duration_hours = slot_capacity_hours

        extended_stay = 1 if duration_hours > 24 else 0
        is_extended_booking = 1 if duration_hours > 24.0 else 0
        commercial_units = float(np.round(duration_hours / 24.0, 2))
        hours_over_24 = max(0.0, float(duration_hours - 24.0))

        if duration_hours <= 13.0:
            duration_bucket = "12H"
        elif duration_hours <= 30.0:
            duration_bucket = "24H"
        elif duration_hours <= 54.0:
            duration_bucket = "48H"
        elif duration_hours <= 78.0:
            duration_bucket = "72H"
        elif duration_hours <= 102.0:
            duration_bucket = "96H"
        else:
            duration_bucket = "120H+"

        selling_price_raw = safe_float(row.get("selling_price"), 0.0)
        if selling_price_raw > 0 and commercial_units > 0:
            effective_daily_rate = float(np.round(selling_price_raw / commercial_units, 2))
        else:
            effective_daily_rate = 8500.0

        if duration_hours <= 24.0:
            extended_discount_ratio = 1.0
        elif duration_hours <= 48.0:
            extended_discount_ratio = 0.95
        elif duration_hours <= 72.0:
            extended_discount_ratio = 0.90
        elif duration_hours <= 96.0:
            extended_discount_ratio = 0.85
        else:
            extended_discount_ratio = 0.80


        slot_utilization_ratio = min(1.0, max(0.1, duration_hours / slot_capacity_hours))
        opportunity_cost_factor = float(np.round(max(0.90, 0.90 + 0.10 * slot_utilization_ratio), 4))

        competitor_diff = 0.0
        if competitor_price > 0:
            competitor_diff = competitor_price - 8500.0 # baseline offset

        # weather forecast variable
        weather_condition = str(row.get("weather_forecast", row.get("weather_condition", "Clear")))

        # V2 features
        is_friday_night = 1 if (day_of_week == 4 and "NIGHT" in slot_type.upper()) else 0
        is_saturday_day = 1 if (day_of_week == 5 and "DAY" in slot_type.upper()) else 0
        is_saturday_night = 1 if (day_of_week == 5 and "NIGHT" in slot_type.upper()) else 0
        is_sunday_day = 1 if (day_of_week == 6 and "DAY" in slot_type.upper()) else 0
        is_sunday_night = 1 if (day_of_week == 6 and "NIGHT" in slot_type.upper()) else 0

        is_holiday_bridge = 1 if (days_before_festival == 1 and day_of_week == 4) or (days_after_festival == 1 and day_of_week == 0) else 0
        wedding_season = 1 if month in [11, 12, 1, 2] else 0

        festival_importance_score = 0.0
        if is_festival:
            f_name = str(festival_name).lower()
            if any(k in f_name for k in ["diwali", "new year", "christmas", "holi", "uttarayan"]):
                festival_importance_score = 1.0
            elif any(k in f_name for k in ["eid", "ganesh", "navratri", "janmashtami"]):
                festival_importance_score = 0.8
            else:
                festival_importance_score = 0.5

        is_same_day = 1 if lead_days == 0 else 0
        is_lead_1_3d = 1 if 1 <= lead_days <= 3 else 0
        is_lead_4_7d = 1 if 4 <= lead_days <= 7 else 0
        is_lead_8_14d = 1 if 8 <= lead_days <= 14 else 0
        is_lead_15_30d = 1 if 15 <= lead_days <= 30 else 0
        is_lead_31_60d = 1 if 31 <= lead_days <= 60 else 0
        is_lead_60d_plus = 1 if lead_days > 60 else 0

        lead_time_demand_curve = 1.0


        # Occupancy Features (fallbacks)
        current_occupancy_pct = safe_float(row.get("current_occupancy_pct"), 0.35)
        remaining_inventory = safe_float(row.get("remaining_inventory"), 10.0)
        booking_pace = safe_float(row.get("booking_pace"), 1.0)
        occupancy_trend = safe_float(row.get("occupancy_trend"), 0.0)

        # Demand Index Forecasting (0 to 100)
        base_index = 30.0
        if is_weekend:
            base_index += 20.0
        if is_festival:
            base_index += 30.0 * festival_importance_score
        if wedding_season:
            base_index += 10.0
        if temp > 33.0 or rain_prob > 50.0:
            base_index -= 15.0
        base_index += current_occupancy_pct * 30.0
        base_index += (booking_pace - 1.0) * 10.0
        demand_index = float(np.clip(base_index, 5.0, 100.0))

        features = {
            "booking_date": dt.strftime("%Y-%m-%d"),
            "month": month,
            "month_sin": month_sin,
            "month_cos": month_cos,
            "year": year,
            "day_of_week": day_of_week,
            "week_of_year": week_of_year,
            "day_of_year": day_of_year,
            "is_weekend": is_weekend,
            "is_festival": is_festival,
            "festival_name": festival_name,
            
            # Intelligent Festival Demand Window Engine Features
            "festival_detected": festival_features["festival_detected"],
            "festival_category": festival_features["festival_category"],
            "festival_tier": festival_features["festival_tier"],
            "festival_demand_level": festival_features["festival_demand_level"],
            "festival_multiplier": festival_features["festival_multiplier"],
            "festival_overlap_hours": festival_features["festival_overlap_hours"],
            "festival_overlap_percentage": festival_features["festival_overlap_percentage"],
            "festival_window_start": festival_features["festival_window_start"],
            "festival_window_end": festival_features["festival_window_end"],
            "is_peak_festival": festival_features["is_peak_festival"],
            "multiple_festival_overlap": festival_features["multiple_festival_overlap"],
            "highest_priority_festival": festival_features["highest_priority_festival"],
            
            "is_festival_eve": is_festival_eve,
            "days_before_festival": days_before_festival,
            "days_after_festival": days_after_festival,
            "is_long_weekend": is_long_weekend,
            "is_consecutive_holiday": is_consecutive_holiday,
            "is_school_vacation": is_school_vacation,
            "is_local_vacation": is_local_vacation,
            "is_vacation": is_vacation,
            "season": season,
            "season_monsoon": season_monsoon,
            "season_summer": season_summer,
            "season_winter": season_winter,
            "is_peak_season": is_peak_season,
            "is_off_season": is_off_season,
            "slot_type": slot_type,
            "commercial_slot": slot_type,
            "slot_capacity_hours": slot_capacity_hours,
            "duration_hours": duration_hours,
            "commercial_units": commercial_units,
            "duration_bucket": duration_bucket,
            "is_extended_booking": is_extended_booking,
            "hours_over_24": hours_over_24,
            "effective_daily_rate": effective_daily_rate,
            "extended_discount_ratio": extended_discount_ratio,
            "extended_stay": extended_stay,
            "slot_utilization_ratio": slot_utilization_ratio,

            "opportunity_cost_factor": opportunity_cost_factor,
            "person_count": person_count,
            "is_couple": is_couple,
            "is_family": is_family,
            "is_corporate": is_corporate,
            "weather_condition": weather_condition,
            "lead_days": lead_days,
            "lead_time_bucket": lead_time_bucket,
            "lead_time_cat": lead_time_cat,
            "competitor_price": competitor_price,
            "competitor_diff": competitor_diff,
            "temperature": temp,
            "rain_probability": rain_prob,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "cloud_cover": cloud_cover,
            "demand_score": demand_score,
            "business_confidence_score": business_confidence_score,
            "month_slot_avg": month_slot_avg,
            "month_weekend_slot_avg": month_weekend_slot_avg,
            "month_guest_slot_avg": month_guest_slot_avg,
            "month_festival_slot_avg": month_festival_slot_avg,
            "month_leadtime_slot_avg": month_leadtime_slot_avg,
            "month_weather_slot_avg": month_weather_slot_avg,
            "hierarchical_fallback_avg": hierarchical_fallback_avg,
            "hierarchical_confidence_score": hierarchical_confidence_score,
            "hierarchical_matched_level": hierarchical_matched_level,

            # Independent Segment Historical Statistics
            "slot_month_weekend_ratio": slot_month_weekend_ratio,
            "slot_month_weekend_diff": slot_month_weekend_diff,
            "segment_mean": segment_mean,
            "segment_median": segment_median,
            "segment_trimmed_mean": segment_trimmed_mean,
            "segment_weighted_median": segment_weighted_median,
            "segment_std": segment_std,
            "segment_count": segment_count,
            "segment_confidence": segment_confidence,
            "p25_price": p25_price,
            "p75_price": p75_price,




            # V2 features
            "is_friday_night": is_friday_night,
            "is_saturday_day": is_saturday_day,
            "is_saturday_night": is_saturday_night,
            "is_sunday_day": is_sunday_day,
            "is_sunday_night": is_sunday_night,
            "is_holiday_bridge": is_holiday_bridge,
            "wedding_season": wedding_season,
            "is_same_day": is_same_day,
            "is_lead_1_3d": is_lead_1_3d,
            "is_lead_4_7d": is_lead_4_7d,
            "is_lead_8_14d": is_lead_8_14d,
            "is_lead_15_30d": is_lead_15_30d,
            "is_lead_31_60d": is_lead_31_60d,
            "is_lead_60d_plus": is_lead_60d_plus,
            "lead_time_demand_curve": lead_time_demand_curve,
            "current_occupancy_pct": current_occupancy_pct,
            "remaining_inventory": remaining_inventory,
            "booking_pace": booking_pace,
            "occupancy_trend": occupancy_trend,
            "demand_index": demand_index,
            "festival_importance_score": festival_importance_score,

            "highest_revenue_weekday": insights.get("highest_revenue_weekday", 6),
            "highest_revenue_month": insights.get("highest_revenue_month", 5),
            "weekend_premium_ratio": weekend_premium,
            "summer_demand_ratio": summer_demand_ratio,
            "winter_demand_ratio": winter_demand_ratio,
            "rain_impact_ratio": rain_impact_ratio
        }
        
        return features

    @classmethod
    def compute_loo_group_metrics(
        cls, df: pd.DataFrame, group_cols: List[str], target_col: str, is_prediction: bool
    ) -> Tuple[np.ndarray, np.ndarray]:
        if "is_festival" not in group_cols and "is_festival" in df.columns:
            base_df = df[df["is_festival"] == 0]
        else:
            base_df = df

        gp = base_df.groupby(group_cols)[target_col].agg(["sum", "count"]).reset_index()
        # Preserve original index alignment
        merged = df[group_cols].reset_index().merge(gp, on=group_cols, how="left").set_index("index")
        
        sum_val = merged.loc[df.index, "sum"].fillna(0).values
        count_val = merged.loc[df.index, "count"].fillna(0).values
        y_val = df[target_col].values
        
        is_included = (df["is_festival"] == 0).values if ("is_festival" not in group_cols and "is_festival" in df.columns) else np.ones(len(df), dtype=bool)
        
        if is_prediction and "_is_prediction_row" in df.columns:
            is_pred_target = df["_is_prediction_row"].values.astype(bool)
            adj_sum = np.where(is_pred_target, sum_val, np.where(is_included, sum_val - y_val, sum_val))
            adj_count = np.where(is_pred_target, count_val, np.where(is_included, count_val - 1, count_val))
        else:
            adj_sum = np.where(is_included, sum_val - y_val, sum_val)
            adj_count = np.where(is_included, count_val - 1, count_val)
            
        mean_val = np.where(adj_count > 0, adj_sum / adj_count, np.nan)
        return mean_val, adj_count

    @classmethod
    def compute_loo_hierarchical_mean(
        cls, df: pd.DataFrame, group_cols: List[str], fallback_col: str, target_col: str, is_prediction: bool
    ) -> pd.Series:
        if "is_festival" not in group_cols and "is_festival" in df.columns:
            base_df = df[df["is_festival"] == 0]
        else:
            base_df = df

        gp = base_df.groupby(group_cols)[target_col].agg(["sum", "count"]).reset_index()
        # Preserve original index alignment
        merged = df[group_cols].reset_index().merge(gp, on=group_cols, how="left").set_index("index")
        
        sum_val = merged.loc[df.index, "sum"].fillna(0).values
        count_val = merged.loc[df.index, "count"].fillna(0).values
        y_val = df[target_col].values
        
        is_included = (df["is_festival"] == 0).values if ("is_festival" not in group_cols and "is_festival" in df.columns) else np.ones(len(df), dtype=bool)
        
        if is_prediction and "_is_prediction_row" in df.columns:
            is_pred_target = df["_is_prediction_row"].values.astype(bool)
            adj_sum = np.where(is_pred_target, sum_val, np.where(is_included, sum_val - y_val, sum_val))
            adj_count = np.where(is_pred_target, count_val, np.where(is_included, count_val - 1, count_val))
        else:
            adj_sum = np.where(is_included, sum_val - y_val, sum_val)
            adj_count = np.where(is_included, count_val - 1, count_val)
            
        mean_val = np.where(adj_count > 0, adj_sum / adj_count, np.nan)
        fallback_series = df[fallback_col].values
        return pd.Series(np.where(np.isnan(mean_val), fallback_series, mean_val), index=df.index)

    @classmethod
    def process_dataframe(cls, df: pd.DataFrame, is_prediction: bool = False, historical_df: pd.DataFrame = None) -> pd.DataFrame:
        df = df.copy()
        
        col_map = {}
        for c in df.columns:
            clean = str(c).strip().lower().replace(" ", "_").replace("-", "_")
            if clean in ["date", "bookingdate", "booking_date", "check_in", "checkin", "checkin_date", "event_date", "day"]:
                col_map[c] = "booking_date"
            elif clean in ["slot", "commercial_slot", "slot_type", "inventory_slot", "timing", "type", "booking_category", "category"]:
                col_map[c] = "commercial_slot"
            elif clean in ["person_count", "guest_count", "guests", "no_of_guests", "persons", "pax", "people", "count"]:
                col_map[c] = "person_count"
            elif clean in ["selling_price", "price", "rent", "farm_price", "booked_price", "booking_amount", "final_price", "price_rs", "rupees", "charges", "total_price", "cost", "rate"]:
                col_map[c] = "selling_price"
            elif clean in ["lead_days", "lead_time", "lead_days_advance", "advance_days"]:
                col_map[c] = "lead_days"
            elif clean in ["competitor_price", "comp_price", "market_price"]:
                col_map[c] = "competitor_price"
            else:
                col_map[c] = clean
        
        df.rename(columns=col_map, inplace=True)
        df = df.loc[:, ~df.columns.duplicated()]

        if "selling_price" not in df.columns:
            for c in df.columns:
                c_str = str(c).lower()
                if "selling_price" in c_str or "booking_price" in c_str or "rent" in c_str or "price" in c_str:
                    df.rename(columns={c: "selling_price"}, inplace=True)
                    break

        if "booking_date" not in df.columns:
            for c in df.columns:
                c_str = str(c).lower()
                if "date" in c_str:
                    df.rename(columns={c: "booking_date"}, inplace=True)
                    break

        if "booking_date" in df.columns:
            df["booking_date"] = pd.to_datetime(df["booking_date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df["booking_date"] = df["booking_date"].fillna(date.today().strftime("%Y-%m-%d"))
        else:
            df["booking_date"] = date.today().strftime("%Y-%m-%d")

        if "commercial_slot" not in df.columns:
            df["commercial_slot"] = "12H_DAY"
        if "person_count" not in df.columns:
            df["person_count"] = 4
        if "lead_days" not in df.columns:
            df["lead_days"] = 7
        
        if "selling_price" not in df.columns:
            df["selling_price"] = 8500.0
        else:
            df["selling_price"] = pd.to_numeric(df["selling_price"], errors="coerce").fillna(8500.0)

        # Drop any raw datetime columns named month/year/day_of_week
        for col_to_drop in ["month", "year", "day_of_week"]:
            if col_to_drop in df.columns:
                df.drop(columns=[col_to_drop], inplace=True)

        # Call compute_advanced_time_series_features to get advanced rolling features (lags, occupancy)
        if len(df) >= 2:
            df = cls.compute_advanced_time_series_features(df)

        # Automatically discover business insights before extracting row features (Phase 5)
        if len(df) > 5 and not is_prediction:
            BusinessInsightDiscoverer.discover_and_save_insights(df)

        # Optimize: if _is_prediction_row is present, only extract features for the new prediction targets
        if "_is_prediction_row" in df.columns:
            target_mask = df["_is_prediction_row"] == True
            df_targets = df[target_mask].copy()
            df_history = df[~target_mask].copy()
            
            features_list = [FeatureEngineer.extract_features_from_dict(row.to_dict()) for _, row in df_targets.iterrows()]
            features_df = pd.DataFrame(features_list)
            
            raw_inputs = ["booking_date", "commercial_slot", "slot_type", "selling_price", "person_count", "duration_hours", "lead_days", "competitor_price", "_is_prediction_row"]
            drop_cols = [c for c in df_targets.columns if c in features_df.columns and c not in raw_inputs]
            df_targets_clean = df_targets.drop(columns=drop_cols).reset_index(drop=True)
            
            # Clean duplicate columns to prevent pandas InvalidIndexError during vertical concatenation
            dup_cols = [c for c in features_df.columns if c in df_targets_clean.columns]
            features_df_clean = features_df.drop(columns=dup_cols)
            
            processed_targets = pd.concat([df_targets_clean, features_df_clean], axis=1)
            combined_df = pd.concat([df_history, processed_targets], ignore_index=True)
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
        else:
            features_list = [FeatureEngineer.extract_features_from_dict(row.to_dict()) for _, row in df.iterrows()]
            features_df = pd.DataFrame(features_list)
            
            raw_inputs = ["booking_date", "commercial_slot", "slot_type", "selling_price", "person_count", "duration_hours", "lead_days", "competitor_price"]
            drop_cols = [c for c in df.columns if c in features_df.columns and c not in raw_inputs]
            df_clean = df.drop(columns=drop_cols).reset_index(drop=True)
            
            combined_df = pd.concat([df_clean, features_df], axis=1)
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]

        # V2 Data-Driven Hierarchical Pricing System (Leakage-Free LOO Target Encoding)
        # Ensure all grouping/target columns are numeric
        combined_df = combined_df.copy()
        combined_df["month"] = pd.to_numeric(combined_df["month"], errors="coerce").fillna(6).astype(int)
        combined_df["is_weekend"] = pd.to_numeric(combined_df["is_weekend"], errors="coerce").fillna(0).astype(int)
        combined_df["is_festival"] = pd.to_numeric(combined_df["is_festival"], errors="coerce").fillna(0).astype(int)
        combined_df["person_count"] = pd.to_numeric(combined_df["person_count"], errors="coerce").fillna(4).astype(int)
        combined_df["lead_days"] = pd.to_numeric(combined_df["lead_days"], errors="coerce").fillna(7).astype(int)
        combined_df["rain_probability"] = pd.to_numeric(combined_df["rain_probability"], errors="coerce").fillna(20.0).astype(float)
        combined_df["selling_price"] = pd.to_numeric(combined_df["selling_price"], errors="coerce").fillna(8500.0).astype(float)
        
        # Define hierarchical matching buckets
        combined_df["guest_bucket"] = np.where(combined_df["person_count"] <= 2, 1,
                                      np.where(combined_df["person_count"] <= 8, 2,
                                      np.where(combined_df["person_count"] <= 15, 3, 4)))
        
        combined_df["lead_bucket"] = np.where(combined_df["lead_days"] <= 3, 1,
                                     np.where(combined_df["lead_days"] <= 14, 2, 3))
        
        combined_df["rain_bucket"] = np.where(combined_df["rain_probability"] > 30.0, 1, 0)
        
        combined_df["festival_bucket"] = np.where(combined_df["is_festival"] == 0, 0,
                                       np.where(combined_df["festival_importance_score"] < 0.6, 1, 2))
                                       
        combined_df["season"] = np.where(combined_df["month"].isin([3, 4, 5]), "summer",
                                np.where(combined_df["month"].isin([6, 7, 8, 9, 10]), "monsoon", "winter"))
                                
        # Calculate overall and slot fallbacks
        y_val = combined_df["selling_price"].values
        total_sum = y_val.sum()
        total_count = len(combined_df)
        
        if is_prediction and "_is_prediction_row" in combined_df.columns:
            is_pred_target = combined_df["_is_prediction_row"].values.astype(bool)
            hist_y = y_val[~is_pred_target]
            hist_sum = hist_y.sum()
            hist_count = len(hist_y)
            overall_sum_adj = np.where(is_pred_target, hist_sum, hist_sum - y_val)
            overall_cnt_adj = np.where(is_pred_target, hist_count, hist_count - 1)
        else:
            overall_sum_adj = total_sum - y_val
            overall_cnt_adj = total_count - 1
            
        l8_mean = np.where(overall_cnt_adj > 0, overall_sum_adj / overall_cnt_adj, 8500.0)
        l8_count = overall_cnt_adj
        
        # Level 7: Slot only
        l7_mean, l7_count = cls.compute_loo_group_metrics(combined_df, ["slot_type"], "selling_price", is_prediction)
        
        # Level 6: Slot + Month
        l6_mean, l6_count = cls.compute_loo_group_metrics(combined_df, ["slot_type", "month"], "selling_price", is_prediction)
        
        # Level 5: Slot + Month + Weekend/Weekday
        l5_mean, l5_count = cls.compute_loo_group_metrics(combined_df, ["slot_type", "month", "is_weekend"], "selling_price", is_prediction)
        
        # Level 4: Slot + Month + Weekend/Weekday + Guest Bucket
        l4_mean, l4_count = cls.compute_loo_group_metrics(combined_df, ["slot_type", "month", "is_weekend", "guest_bucket"], "selling_price", is_prediction)
        
        # Level 3: Slot + Month + Weekend/Weekday + Guest Bucket + Festival Tier
        l3_mean, l3_count = cls.compute_loo_group_metrics(combined_df, ["slot_type", "month", "is_weekend", "guest_bucket", "festival_bucket"], "selling_price", is_prediction)
        
        # Level 2: Slot + Month + Weekend/Weekday + Guest Bucket + Festival Tier + Lead Time Bucket
        l2_mean, l2_count = cls.compute_loo_group_metrics(
            combined_df, ["slot_type", "month", "is_weekend", "guest_bucket", "festival_bucket", "lead_bucket"], "selling_price", is_prediction
        )
        
        # Level 1: Slot + Month + Weekend/Weekday + Guest Bucket + Festival Tier + Lead Time Bucket + Weather Pattern
        l1_mean, l1_count = cls.compute_loo_group_metrics(
            combined_df, ["slot_type", "month", "is_weekend", "guest_bucket", "festival_bucket", "lead_bucket", "rain_bucket"], "selling_price", is_prediction
        )
        
        # Traversing the matching chain for hierarchical fallback mean (min_samples = 3)
        MIN_RECORDS = 3
        final_mean = l8_mean
        final_level = np.full(len(combined_df), 8, dtype=int)
        final_count = l8_count
        
        levels_data = [
            (7, l7_mean, l7_count),
            (6, l6_mean, l6_count),
            (5, l5_mean, l5_count),
            (4, l4_mean, l4_count),
            (3, l3_mean, l3_count),
            (2, l2_mean, l2_count),
            (1, l1_mean, l1_count)
        ]
        
        for lvl_idx, lvl_mean, lvl_count in levels_data:
            mask = lvl_count >= MIN_RECORDS
            final_mean = np.where(mask, lvl_mean, final_mean)
            final_level = np.where(mask, lvl_idx, final_level)
            final_count = np.where(mask, lvl_count, final_count)
            
        combined_df["hierarchical_fallback_avg"] = final_mean
        
        # Confidence score mapping:
        # base_conf = {1: 0.90, 2: 0.80, 3: 0.70, 4: 0.60, 5: 0.50, 6: 0.40, 7: 0.30, 8: 0.10}
        base_conf_map = np.array([0.0, 0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.10])
        base_confs = base_conf_map[final_level]
        
        # Calculate adjustment based on sample count
        count_adj = 0.10 * np.minimum(1.0, (final_count - 3) / 10.0)
        count_adj = np.where(final_level == 8, 0.10 * np.minimum(1.0, final_count / 10.0), count_adj)
        
        combined_df["hierarchical_confidence_score"] = base_confs + count_adj
        combined_df["hierarchical_matched_level"] = final_level
        
        # Compute individual leakage-free segment averages
        slot_fallback = np.where(l7_count > 0, l7_mean, l8_mean)
        
        # month_slot_avg (Same Month + Same Slot)
        combined_df["month_slot_avg"] = np.where(l6_count > 0, l6_mean, slot_fallback)
        
        m_we_mean, m_we_count = cls.compute_loo_group_metrics(combined_df, ["month", "is_weekend", "slot_type"], "selling_price", is_prediction)
        combined_df["month_weekend_slot_avg"] = np.where(m_we_count > 0, m_we_mean, combined_df["month_slot_avg"].values)
        
        m_g_mean, m_g_count = cls.compute_loo_group_metrics(combined_df, ["month", "guest_bucket", "slot_type"], "selling_price", is_prediction)
        combined_df["month_guest_slot_avg"] = np.where(m_g_count > 0, m_g_mean, combined_df["month_slot_avg"].values)
        
        m_f_mean, m_f_count = cls.compute_loo_group_metrics(combined_df, ["month", "is_festival", "slot_type"], "selling_price", is_prediction)
        combined_df["month_festival_slot_avg"] = np.where(m_f_count > 0, m_f_mean, combined_df["month_slot_avg"].values)
        
        m_l_mean, m_l_count = cls.compute_loo_group_metrics(combined_df, ["month", "lead_bucket", "slot_type"], "selling_price", is_prediction)
        combined_df["month_leadtime_slot_avg"] = np.where(m_l_count > 0, m_l_mean, combined_df["month_slot_avg"].values)
        
        m_w_mean, m_w_count = cls.compute_loo_group_metrics(combined_df, ["month", "rain_bucket", "slot_type"], "selling_price", is_prediction)
        combined_df["month_weather_slot_avg"] = np.where(m_w_count > 0, m_w_mean, combined_df["month_slot_avg"].values)
        
        # Drop temporary LOO / bucket columns to keep dataset clean
        combined_df.drop(columns=["guest_bucket", "lead_bucket", "rain_bucket", "festival_bucket", "season_monsoon", "season_summer", "season_winter"], inplace=True)
        
        # Add Strict Rolling Features
        if historical_df is not None and not historical_df.empty:
            ref_df = historical_df.copy()
            if 'booking_date' in ref_df.columns:
                ref_df['booking_date'] = pd.to_datetime(ref_df['booking_date'])
            ref_df = ref_df.sort_values('booking_date')
            global_median = ref_df['selling_price'].median()
        else:
            ref_df = pd.DataFrame()
            global_median = 8500.0

        if 'booking_date' in combined_df.columns:
            combined_df['booking_date_dt'] = pd.to_datetime(combined_df['booking_date'])
        else:
            combined_df['booking_date_dt'] = pd.to_datetime('today')

        density_col = []
        momentum_col = []
        variance_col = []
        
        for i, row in combined_df.iterrows():
            b_date = row['booking_date_dt']
            slot = row.get('commercial_slot', '12H Day')
            
            if not ref_df.empty and 'booking_date' in ref_df.columns:
                past_bookings = ref_df[ref_df['booking_date'] < b_date]
                sim_past = past_bookings[past_bookings['commercial_slot'] == slot]
                
                window_start = b_date - pd.Timedelta(days=30)
                sim_30d = sim_past[sim_past['booking_date'] >= window_start]
                
                density_col.append(len(sim_30d))
                
                if len(sim_30d) > 0:
                    momentum_col.append(sim_30d['selling_price'].mean())
                else:
                    # Fallback to historical expanding median to prevent target leakage
                    if len(past_bookings) > 0:
                        momentum_col.append(past_bookings['selling_price'].median())
                    else:
                        momentum_col.append(global_median)
                        
                if len(sim_past) > 1:
                    variance_col.append(sim_past['selling_price'].std())
                else:
                    variance_col.append(0)
            else:
                density_col.append(0)
                momentum_col.append(global_median)
                variance_col.append(0)

        combined_df['similar_booking_density_30d'] = density_col
        combined_df['price_momentum_30d'] = momentum_col
        combined_df['historical_variance'] = variance_col
        
        if 'days_before_festival' in combined_df.columns:
            combined_df['is_near_holiday'] = (combined_df['days_before_festival'] <= 3).astype(int)
        else:
            combined_df['is_near_holiday'] = 0

        combined_df.drop(columns=['booking_date_dt'], inplace=True, errors='ignore')

        return combined_df

    @classmethod
    def _load_festival_intelligence(cls) -> Dict[str, float]:
        import json
        from pathlib import Path
        fest_path = Path("data/learned_festival_intelligence.json")
        if fest_path.exists():
            try:
                with open(fest_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
