import pandas as pd
import json
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Tuple
from app.config import DATA_DIR

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
        "01-01": "New Year Day", "01-26": "Republic Day", "03-25": "Holi",
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
        except Exception as ex:
            print(f"⚠️ Error discovering business insights: {ex}")

class FeatureEngineer:
    _insights = None

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
        year = int(dt.year)
        day_of_week = int(dt.weekday()) # 0 = Monday, 6 = Sunday
        is_weekend = 1 if day_of_week in [5, 6] else 0

        full_date_str = dt.strftime("%Y-%m-%d")
        month_day = dt.strftime("%m-%d")

        festival_name = FESTIVALS.get(full_date_str) or FESTIVALS.get(month_day, "")
        is_festival = 1 if festival_name else 0
        is_festival_eve = 1 if (full_date_str in FESTIVAL_EVES or month_day in FESTIVAL_EVES) else 0
        is_vacation = 1 if month in [5, 12, 1] else 0

        # Season
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
        
        # Couple Discount Logic
        is_couple = 1 if person_count <= 2 else 0
        is_family = 1 if 3 <= person_count <= 12 else 0
        is_corporate = 1 if person_count > 12 else 0

        commercial_slot = str(row.get("commercial_slot", "12H_DAY"))
        
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

        # Calculate Days Before & Days After Festival
        days_before_festival = 7
        days_after_festival = 7
        try:
            for offset in range(1, 8):
                b_dt = (dt + pd.Timedelta(days=offset)).strftime("%Y-%m-%d")
                b_md = (dt + pd.Timedelta(days=offset)).strftime("%m-%d")
                if b_dt in FESTIVALS or b_md in FESTIVALS:
                    days_before_festival = offset
                    break
            for offset in range(1, 8):
                a_dt = (dt - pd.Timedelta(days=offset)).strftime("%Y-%m-%d")
                a_md = (dt - pd.Timedelta(days=offset)).strftime("%m-%d")
                if a_dt in FESTIVALS or a_md in FESTIVALS:
                    days_after_festival = offset
                    break
        except Exception:
            pass

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

        slot_code = str(row.get("commercial_slot", "12H_DAY")).upper().strip().replace(" ", "_")
        slot_capacity_hours = 24.0 if "24H" in slot_code else 12.0
        duration_hours = safe_float(row.get("duration_hours"), slot_capacity_hours)
        if duration_hours <= 0:
            duration_hours = slot_capacity_hours

        slot_utilization_ratio = min(1.0, max(0.1, duration_hours / slot_capacity_hours))
        opportunity_cost_factor = float(np.round(max(0.90, 0.90 + 0.10 * slot_utilization_ratio), 4))

        competitor_diff = 0.0
        if competitor_price > 0:
            # We will approximate this or compute directly
            competitor_diff = competitor_price - 8500.0 # baseline offset

        return {
            "booking_date": dt.strftime("%Y-%m-%d"),
            "month": month,
            "year": year,
            "day_of_week": day_of_week,
            "week_of_year": week_of_year,
            "day_of_year": day_of_year,
            "is_weekend": is_weekend,
            "is_festival": is_festival,
            "festival_name": festival_name,
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
            "commercial_slot": commercial_slot,
            "slot_capacity_hours": slot_capacity_hours,
            "duration_hours": duration_hours,
            "slot_utilization_ratio": slot_utilization_ratio,
            "opportunity_cost_factor": opportunity_cost_factor,
            "person_count": person_count,
            "is_couple": is_couple,
            "is_family": is_family,
            "is_corporate": is_corporate,
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
            "highest_revenue_weekday": insights.get("highest_revenue_weekday", 6),
            "highest_revenue_month": insights.get("highest_revenue_month", 5),
            "weekend_premium_ratio": weekend_premium,
            "summer_demand_ratio": summer_demand_ratio,
            "winter_demand_ratio": winter_demand_ratio,
            "rain_impact_ratio": rain_impact_ratio
        }

    @staticmethod
    def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches a raw booking DataFrame with full engineered features.
        STRICT EXPLICIT PRICE HEADER MAPPING (prevents mapping random 'val' or 'total' columns).
        """
        df = df.copy()
        
        col_map = {}
        for c in df.columns:
            clean = str(c).strip().lower().replace(" ", "_").replace("-", "_")
            if clean in ["date", "bookingdate", "booking_date", "check_in", "checkin", "checkin_date", "event_date", "day"]:
                col_map[c] = "booking_date"
            elif clean in ["slot", "commercial_slot", "slot_type", "inventory_slot", "timing", "type"]:
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

        # Automatically discover business insights before extracting row features (Phase 5)
        if len(df) > 5:
            BusinessInsightDiscoverer.discover_and_save_insights(df)

        features_list = [FeatureEngineer.extract_features_from_dict(row.to_dict()) for _, row in df.iterrows()]
        features_df = pd.DataFrame(features_list)

        combined_df = pd.concat([df.reset_index(drop=True), features_df], axis=1)
        combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]

        return combined_df
