import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from app.config import DATA_DIR
from app.services.feature_engineering import FeatureEngineer, safe_int, safe_float
from app.database import SessionLocal
from app.models.db_models import BookingRecord

CLEAN_DATA_PATH = DATA_DIR / "clean_booking_data.csv"
SAMPLE_EXCEL_PATH = DATA_DIR / "Farm_Booking_Data.xlsx"

class DataPipeline:
    @staticmethod
    def has_user_data() -> bool:
        """
        Checks if a user dataset file exists and has records.
        """
        if CLEAN_DATA_PATH.exists():
            try:
                df = pd.read_csv(CLEAN_DATA_PATH)
                return not df.empty
            except Exception:
                return False
        return False

    @staticmethod
    def generate_synthetic_historical_data(num_records: int = 500) -> pd.DataFrame:
        """
        Generates realistic 2-year historical farmhouse booking dataset for initial template download.
        USES EXCLUSIVELY COMMERCIAL SLOTS - NEVER HOURLY PRICING.
        Includes 12H_DAY, 12H_NIGHT, 24H_DAY, 24H_NIGHT, COUPLE_SLOT, COUPLE_DAY, COUPLE_NIGHT.
        """
        np.random.seed(42)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        dates = [start_date + timedelta(days=int(i)) for i in np.random.randint(0, 730, num_records)]
        dates.sort()

        slots = ["12H_DAY", "12H_NIGHT", "24H_DAY", "24H_NIGHT", "COUPLE_SLOT", "COUPLE_DAY", "COUPLE_NIGHT"]
        slot_probs = [0.25, 0.25, 0.15, 0.15, 0.08, 0.06, 0.06]

        records = []
        for dt in dates:
            booking_date_str = dt.strftime("%Y-%m-%d")
            slot = np.random.choice(slots, p=slot_probs)
            
            if slot in ["COUPLE_SLOT", "COUPLE_DAY"]:
                person_count = 2
                duration = 12.0
                base_price = 3500.0
            elif slot == "COUPLE_NIGHT":
                person_count = 2
                duration = 12.0
                base_price = 4200.0
            elif slot == "12H_DAY":
                person_count = np.random.randint(4, 25)
                duration = 12.0
                base_price = 8000.0
            elif slot == "12H_NIGHT":
                person_count = np.random.randint(4, 25)
                duration = 12.0
                base_price = 9500.0
            elif slot == "24H_DAY":
                person_count = np.random.randint(4, 30)
                duration = 24.0
                base_price = 14500.0
            else: # 24H_NIGHT
                person_count = np.random.randint(4, 30)
                duration = 24.0
                base_price = 16000.0

            lead_days = int(np.random.exponential(scale=10.0))
            lead_days = min(90, max(0, lead_days))

            month = dt.month
            is_weekend = 1 if dt.weekday() in [5, 6] else 0

            multiplier = 1.0
            if is_weekend: multiplier += 0.25
            if month in [12, 5, 10]: multiplier += 0.20
            if lead_days <= 2: multiplier += 0.10
            if person_count > 15: multiplier += 0.15
            if person_count <= 2: multiplier -= 0.18

            comp_diff = np.random.normal(0, 500)
            selling_price = round(base_price * multiplier + np.random.normal(0, 300), -1)
            competitor_price = round(selling_price + comp_diff, -1)

            if 6 <= month <= 9:
                temp = round(24.0 + np.random.normal(0, 2), 1)
                rain_prob = round(np.random.uniform(60, 95), 1)
                humidity = 85.0
                cond = "Rainy"
            elif 3 <= month <= 5:
                temp = round(33.0 + np.random.normal(0, 2), 1)
                rain_prob = round(np.random.uniform(0, 20), 1)
                humidity = 50.0
                cond = "Sunny"
            else:
                temp = round(22.0 + np.random.normal(0, 2), 1)
                rain_prob = round(np.random.uniform(0, 10), 1)
                humidity = 55.0
                cond = "Clear"

            records.append({
                "booking_date": booking_date_str,
                "commercial_slot": slot,
                "person_count": person_count,
                "duration_hours": duration,
                "lead_days": lead_days,
                "selling_price": max(2500.0, selling_price),
                "competitor_price": max(0.0, competitor_price),
                "temperature": temp,
                "rain_probability": rain_prob,
                "humidity": humidity,
                "weather_condition": cond
            })

        df = pd.DataFrame(records)
        df.to_excel(SAMPLE_EXCEL_PATH, index=False)
        return df

    @classmethod
    def load_raw_dataframe(cls, file_path: Path) -> pd.DataFrame:
        if file_path.suffix in [".xlsx", ".xls"]:
            try:
                excel_file = pd.ExcelFile(file_path)
                
                # Automatically extract Festival_List tab if present in Excel
                for sheet in excel_file.sheet_names:
                    if "festiv" in sheet.lower():
                        try:
                            df_f = pd.read_excel(excel_file, sheet)
                            d_col = next((c for c in df_f.columns if "date" in str(c).lower()), df_f.columns[0])
                            name_col = next((c for c in df_f.columns if any(k in str(c).lower() for k in ["fest", "name", "event"])), df_f.columns[-1])
                            
                            df_f["date"] = pd.to_datetime(df_f[d_col], errors="coerce").dt.strftime("%Y-%m-%d")
                            df_f["festival_name"] = df_f[name_col]
                            df_f["demand_multiplier"] = 1.25
                            df_f["is_eve"] = df_f["festival_name"].astype(str).str.lower().str.contains("eve").astype(int)
                            
                            out_f = df_f[["date", "festival_name", "demand_multiplier", "is_eve"]].dropna(subset=["date"])
                            fest_csv_path = DATA_DIR / "festivals.csv"
                            out_f.to_csv(fest_csv_path, index=False)
                            print(f"🎉 [FESTIVAL EXTRACTOR] Automatically extracted {len(out_f)} festival dates from '{sheet}' tab to '{fest_csv_path.name}'")
                        except Exception as ef:
                            print(f"⚠️ Festival list extraction skipped: {ef}")

                target_sheet = excel_file.sheet_names[0]
                for sheet in excel_file.sheet_names:
                    s_lower = sheet.lower()
                    if any(k in s_lower for k in ["raw", "event", "booking", "transaction", "data"]):
                        target_sheet = sheet
                        break
                df = pd.read_excel(file_path, sheet_name=target_sheet)
                print(f"📖 [DATA PIPELINE] Loaded Excel sheet '{target_sheet}' ({len(df)} rows) from {file_path.name}")
            except Exception as e:
                df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        df.drop_duplicates(inplace=True)
        df.dropna(how="all", inplace=True)
        return df

    @classmethod
    def normalize_commercial_slot(cls, slot_val: Any) -> str:
        s = str(slot_val).upper().strip().replace(" ", "_")
        if "12H_DAY" in s or "12_HR_DAY" in s or "12_HOUR_DAY" in s or "HALF_DAY" in s or "DAY_SLOT" in s:
            return "12H_DAY"
        if "12H_NIGHT" in s or "12_HR_NIGHT" in s or "12_HOUR_NIGHT" in s or "NIGHT_SLOT" in s:
            return "12H_NIGHT"
        if "24H_DAY" in s or "24_HR_DAY" in s or "24_HOUR_DAY" in s or "24H_FULL" in s:
            return "24H_DAY"
        if "24H_NIGHT" in s or "24_HR_NIGHT" in s or "24_HOUR_NIGHT" in s:
            return "24H_NIGHT"
        if "COUPLE_DAY" in s:
            return "COUPLE_DAY"
        if "COUPLE_NIGHT" in s:
            return "COUPLE_NIGHT"
        if "COUPLE" in s or "6H_COUPLE" in s or "COUPLE_SLOT" in s:
            return "COUPLE_SLOT"
        if "WEDDING" in s:
            return "WEDDING_EVENT"
        if "CORPORATE" in s:
            return "CORPORATE_EVENT"
        if "POOL" in s:
            return "POOL_PARTY"
        return s

    @classmethod
    def process_with_explicit_mapping(
        cls,
        file_path: Path,
        price_col: str,
        date_col: str,
        slot_col: Optional[str] = None,
        guests_col: Optional[str] = None,
        lead_col: Optional[str] = None,
        competitor_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Processes uploaded dataset using MANUALLY CONFIRMED column mappings.
        Guarantees NO target guessing!
        """
        df = cls.load_raw_dataframe(file_path)

        mapped_df = pd.DataFrame()

        # 1. Selling Price (CONFIRMED)
        if price_col not in df.columns:
            raise ValueError(f"Selected price column '{price_col}' not found in uploaded file.")
        mapped_df["selling_price"] = pd.to_numeric(df[price_col], errors="coerce").fillna(0.0)

        # 2. Booking Date (CONFIRMED)
        if date_col not in df.columns:
            raise ValueError(f"Selected date column '{date_col}' not found in uploaded file.")
        mapped_df["booking_date"] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
        mapped_df["booking_date"] = mapped_df["booking_date"].fillna(date.today().strftime("%Y-%m-%d"))

        # 3. Commercial Slot Standardisation & Duration-based Inference (Phase 2 & 4)
        if slot_col and slot_col in df.columns:
            mapped_df["commercial_slot"] = df[slot_col].apply(cls.normalize_commercial_slot)
        else:
            # Auto-infer from duration columns if available
            dur_col = next((c for c in df.columns if any(k in str(c).lower() for k in ["duration", "hours", "stay"])), None)
            guests_series = pd.to_numeric(df[guests_col], errors="coerce").fillna(4) if guests_col and guests_col in df.columns else pd.Series([4] * len(df))
            
            if dur_col:
                durations = pd.to_numeric(df[dur_col], errors="coerce").fillna(12.0)
                inferred_slots = []
                for d, g in zip(durations, guests_series):
                    if g <= 2:
                        inferred_slots.append("COUPLE_SLOT")
                    elif d <= 12:
                        inferred_slots.append("12H_DAY")
                    else:
                        inferred_slots.append("24H_DAY")
                mapped_df["commercial_slot"] = inferred_slots
            else:
                mapped_df["commercial_slot"] = "12H_DAY"

        # 4. Guest Count
        if guests_col and guests_col in df.columns:
            mapped_df["person_count"] = pd.to_numeric(df[guests_col], errors="coerce").fillna(4).astype(int)
        else:
            mapped_df["person_count"] = 4

        # 5. Lead Days
        if lead_col and lead_col in df.columns:
            mapped_df["lead_days"] = pd.to_numeric(df[lead_col], errors="coerce").fillna(7).astype(int)
        else:
            mapped_df["lead_days"] = 7

        # 6. Competitor Price
        if competitor_col and competitor_col in df.columns:
            mapped_df["competitor_price"] = pd.to_numeric(df[competitor_col], errors="coerce").fillna(0.0)
        else:
            mapped_df["competitor_price"] = 0.0

        # Filter invalid rows (price <= 0)
        mapped_df = mapped_df[mapped_df["selling_price"] > 0].copy()

        # Run feature engineering
        enriched_df = FeatureEngineer.process_dataframe(mapped_df)
        enriched_df.to_csv(CLEAN_DATA_PATH, index=False)
        cls.sync_to_db(enriched_df)

        return enriched_df

    @classmethod
    def load_and_process_file(cls, file_path: Path) -> pd.DataFrame:
        df = cls.load_raw_dataframe(file_path)
        cols = [str(c) for c in df.columns]
        
        price_col = next((c for c in cols if any(k in c.lower() for k in ["extracted rent", "selling_price", "rent", "price", "booked_price", "booking_amount"])), cols[0])
        date_col = next((c for c in cols if any(k in c.lower() for k in ["start date", "booking_date", "date", "check_in", "checkin"])), cols[0])
        slot_col = next((c for c in cols if any(k in c.lower() for k in ["booking_category", "commercial_slot", "slot", "timing", "category"])), None)
        guests_col = next((c for c in cols if any(k in c.lower() for k in ["person_count", "guest", "person", "pax", "count"])), None)
        lead_col = next((c for c in cols if any(k in c.lower() for k in ["lead_days", "lead"])), None)
        competitor_col = next((c for c in cols if any(k in c.lower() for k in ["competitor_price", "competitor"])), None)

        print(f"🔍 [AUTO DETECT] Auto-detected columns in '{file_path.name}': price='{price_col}', date='{date_col}', slot='{slot_col}'")

        return cls.process_with_explicit_mapping(
            file_path=file_path,
            price_col=price_col,
            date_col=date_col,
            slot_col=slot_col,
            guests_col=guests_col,
            lead_col=lead_col,
            competitor_col=competitor_col
        )

    @staticmethod
    def sync_to_db(df: pd.DataFrame):
        db = SessionLocal()
        try:
            db.query(BookingRecord).delete()
            db.commit()

            records = []
            for _, row in df.iterrows():
                b_date = str(row.get("booking_date"))
                if len(b_date) > 10:
                    b_date = b_date[:10]

                rec = BookingRecord(
                    booking_date=b_date,
                    commercial_slot=str(row.get("commercial_slot", "12H_DAY")),
                    person_count=safe_int(row.get("person_count"), 4),
                    lead_days=safe_int(row.get("lead_days"), 7),
                    duration_hours=safe_float(row.get("duration_hours"), 12.0),
                    selling_price=safe_float(row.get("selling_price"), 8500.0),
                    competitor_price=safe_float(row.get("competitor_price"), 0.0),
                    month=safe_int(row.get("month"), 8),
                    day_of_week=safe_int(row.get("day_of_week"), 5),
                    is_weekend=bool(row.get("is_weekend", True)),
                    is_holiday=bool(row.get("is_festival", False)),
                    is_festival=bool(row.get("is_festival", False)),
                    is_festival_eve=bool(row.get("is_festival_eve", False)),
                    is_vacation=bool(row.get("is_vacation", False)),
                    season=str(row.get("season", "Monsoon")),
                    temperature=safe_float(row.get("temperature"), 26.0),
                    rain_probability=safe_float(row.get("rain_probability"), 20.0),
                    humidity=safe_float(row.get("humidity"), 60.0),
                    weather_condition=str(row.get("weather_condition", "Clear"))
                )
                records.append(rec)
            
            db.bulk_save_objects(records)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
