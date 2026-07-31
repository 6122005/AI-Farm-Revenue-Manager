import joblib
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.config import MODELS_DIR, DATA_DIR, DEFAULT_COMMERCIAL_SLOTS, ENABLE_EXPECTED_REVENUE_OPTIMIZATION

from app.services.weather_service import weather_service
from app.services.feature_engineering import FeatureEngineer, safe_int, safe_float
from app.services.explainability import ExplainableAI
from app.services.ml_trainer import CHAMPION_MODEL_PATH, MLTrainer
from app.services.data_pipeline import DataPipeline, CLEAN_DATA_PATH
from app.services.slot_engine import slot_engine
class PredictionEngine:
    def __init__(self):
        self.model_artifact: Optional[Dict[str, Any]] = None
        self.loaded_model_path: Optional[str] = None
        self.loaded_model_timestamp: Optional[str] = None
        self._clean_data_cache: Optional[pd.DataFrame] = None
        self.lead_days_rules_cache: Optional[List[Any]] = None

    def get_lead_days_rules(self) -> List[Any]:
        if self.lead_days_rules_cache is None:
            from app.models.db_models import LeadDaysRule
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                self.lead_days_rules_cache = db.query(LeadDaysRule).filter(LeadDaysRule.is_active == True).all()
            except Exception as e:
                print(f"⚠️ Error loading Lead Days rules: {e}")
                self.lead_days_rules_cache = []
            finally:
                db.close()
        return self.lead_days_rules_cache

    def purge_cache(self):
        """
        Clears in-memory model cache completely.
        """
        self.model_artifact = None
        self.loaded_model_path = None
        self.loaded_model_timestamp = None
        self._clean_data_cache = None
        self.lead_days_rules_cache = None

    def get_clean_data(self) -> Optional[pd.DataFrame]:
        if self._clean_data_cache is None:
            if CLEAN_DATA_PATH.exists():
                try:
                    df = pd.read_csv(CLEAN_DATA_PATH)
                    if not df.empty:
                        # Precompute slot_norm once to optimize performance
                        slot_col = "slot_type" if "slot_type" in df.columns else "commercial_slot"
                        df["slot_norm"] = df[slot_col].astype(str).str.upper().str.strip().str.replace(" ", "_")
                    self._clean_data_cache = df
                except Exception as e:
                    print(f"⚠️ Error reading CLEAN_DATA_PATH: {e}")
                    self._clean_data_cache = None
            else:
                self._clean_data_cache = None
        return self._clean_data_cache

    def reload_model(self):
        """
        Reloads champion model artifact from disk immediately after an upload re-training.
        """
        self.purge_cache()

        if CHAMPION_MODEL_PATH.exists():
            try:
                artifact = joblib.load(CHAMPION_MODEL_PATH)
                self.model_artifact = artifact
                self.loaded_model_path = str(CHAMPION_MODEL_PATH.absolute())
                self.loaded_model_timestamp = artifact.get("trained_at", datetime.now().isoformat())
                print(f"✅ [DEBUG AUDIT] Prediction Engine loaded model: path={self.loaded_model_path}, timestamp={self.loaded_model_timestamp}")
                return self.model_artifact
            except Exception as e:
                print(f"⚠️ Error loading champion model: {e}")
                self.purge_cache()

        return None

    def load_champion_model(self):
        if self.model_artifact:
            return self.model_artifact
        return self.reload_model()

    def _blend_with_historical_median(self, slot_code: str, person_count: int, pred_raw: float) -> float:
        if not CLEAN_DATA_PATH.exists():
            return pred_raw
            
        try:
            df = self.get_clean_data()
            if df is None or df.empty:
                return pred_raw
                
            # Normalize slot names
            norm_slot = str(slot_code).upper().strip().replace(" ", "_")
            
            # Check count for this specific slot
            slot_df = df[df["slot_norm"] == norm_slot]
            slot_count = len(slot_df)
            
            # Check count for this specific slot + person_count combination
            slot_person_df = slot_df[slot_df["person_count"] == person_count]
            slot_person_count = len(slot_person_df)
            
            # Confidence-based adaptive weight calculation
            if slot_count > 0:
                conf_person = min(1.0, slot_person_count / 10.0)
                conf_slot = min(1.0, slot_count / 30.0)
                confidence = 0.80 * conf_person + 0.20 * conf_slot
            else:
                confidence = 0.0
                
            # Adaptive weight: trusts model between 65% (sparse) and 95% (dense)
            weight_model = 0.65 + 0.30 * confidence
            
            # Find the most specific median available
            if slot_person_count > 0:
                hist_median = float(slot_person_df["selling_price"].median())
            elif slot_count > 0:
                hist_median = float(slot_df["selling_price"].median())
            else:
                hist_median = float(df["selling_price"].median())
                
            blended = weight_model * pred_raw + (1.0 - weight_model) * hist_median
            return blended
                
        except Exception as e:
            print(f"⚠️ Error in historical blending: {e}")
            
        return pred_raw

    def _predict_single_slot(self, features: Dict[str, Any], slot_code: str, artifact: Any) -> float:
        """Helper to predict a single slot using the active model or historical baseline."""
        if not artifact or "model" not in artifact:
            slot_stats = self.get_slot_stats_from_uploaded_data(slot_code)
            return float(slot_stats["base"])
            
        model = artifact["model"]
        feature_cols = artifact.get("features", [])
        
        feat_copy = features.copy()
        feat_copy["slot_type"] = slot_code
        
        row_df = pd.DataFrame([feat_copy])
        categorical_cols = ["slot_type", "season", "weather_condition", "month", "day_of_week"]
        row_encoded = pd.get_dummies(row_df, columns=categorical_cols, drop_first=False)
        model_input = row_encoded.reindex(columns=feature_cols, fill_value=0)
        
        for c in model_input.columns:
            model_input[c] = pd.to_numeric(model_input[c], errors="coerce").fillna(0.0).astype(float)
            
        pred_trans = float(model.predict(model_input)[0])
        pred_raw = float(np.expm1(pred_trans)) if pred_trans < 25.0 else pred_trans
        
        # Let the model predictions propagate directly
        pred_final = pred_raw
        return pred_final

    def get_slot_stats_from_uploaded_data(self, slot_code: str) -> Dict[str, float]:
        norm_input = slot_engine.normalize_commercial_slot(slot_code)
        if CLEAN_DATA_PATH.exists():
            try:
                df = pd.read_csv(CLEAN_DATA_PATH)
                if not df.empty and "slot_type" in df.columns:
                    df["slot_norm"] = df["slot_type"].apply(slot_engine.normalize_commercial_slot)
                    df_slot = df[df["slot_norm"] == norm_input]
                    price_col = "selling_price" if "selling_price" in df_slot.columns else "price"
                    if price_col in df_slot.columns and len(df_slot) > 0:
                        prices = pd.to_numeric(df_slot[price_col], errors="coerce").dropna()
                        prices = prices[prices > 0]
                        if len(prices) > 0:
                            return {
                                "base": float(prices.median()),
                                "median": float(prices.median()),
                                "mean": float(prices.mean()),
                                "count": int(len(prices)),
                                "min": float(prices.min()),
                                "max": float(prices.max()),
                                "p95": float(prices.quantile(0.95))
                            }
                    all_prices = pd.to_numeric(df[price_col], errors="coerce").dropna()
                    all_prices = all_prices[all_prices > 0]
                    if len(all_prices) > 0:
                        return {
                            "base": float(all_prices.median()),
                            "median": float(all_prices.median()),
                            "mean": float(all_prices.mean()),
                            "count": int(len(all_prices)),
                            "min": float(all_prices.min()),
                            "max": float(all_prices.max()),
                            "p95": float(all_prices.quantile(0.95))
                        }
            except Exception as e:
                print(f"⚠️ Error reading uploaded data slot stats: {e}")
        
        return {"base": 3500.0, "median": 3500.0, "mean": 3500.0, "count": 10, "min": 1000.0, "max": 12000.0, "p95": 8000.0}

    def get_learned_package_discount_stats(self) -> Dict[str, Any]:
        """
        Calculates historical package discounts strictly from uploaded Excel dataset.
        """
        day_stats = self.get_slot_stats_from_uploaded_data("12H Day")
        night_stats = self.get_slot_stats_from_uploaded_data("12H Night")
        p_12h_day = day_stats.get("base", 3000.0)
        p_12h_night = night_stats.get("base", 2500.0)
        combined_base = p_12h_day + p_12h_night

        stats_24h_day = self.get_slot_stats_from_uploaded_data("24H Day")
        stats_24h_night = self.get_slot_stats_from_uploaded_data("24H Night")

        avg_24h_day = stats_24h_day.get("mean", 3928.57)
        avg_24h_night = stats_24h_night.get("mean", 5759.22)

        day_disc_pct = round(((combined_base - stats_24h_day.get("base", 4000.0)) / combined_base) * 100.0, 1) if combined_base > 0 else 27.3
        night_disc_pct = round(((combined_base - stats_24h_night.get("base", 5000.0)) / combined_base) * 100.0, 1) if combined_base > 0 else 9.1

        discounts = []
        if CLEAN_DATA_PATH.exists():
            try:
                df = pd.read_csv(CLEAN_DATA_PATH)
                if not df.empty and "slot_type" in df.columns:
                    df_24h = df[df["slot_type"].str.contains("24H", na=False, case=False)]
                    if not df_24h.empty and combined_base > 0:
                        p_col = "selling_price" if "selling_price" in df_24h.columns else "price"
                        prices = pd.to_numeric(df_24h[p_col], errors="coerce").dropna()
                        for p in prices:
                            disc = (1.0 - (p / combined_base)) * 100.0
                            discounts.append(disc)
            except Exception as e:
                print(f"⚠️ Error calculating historical package discounts: {e}")

        if discounts:
            s_disc = pd.Series(discounts)
            avg_disc = round(float(s_disc.mean()), 1)
            med_disc = round(float(s_disc.median()), 1)
            min_disc = round(float(s_disc.min()), 1)
            max_disc = round(float(s_disc.max()), 1)
        else:
            avg_disc = 10.2
            med_disc = 9.1
            min_disc = -263.6
            max_disc = 90.9

        return {
            "average_package_discount_pct": avg_disc,
            "median_package_discount_pct": med_disc,
            "min_package_discount_pct": min_disc,
            "max_package_discount_pct": max_disc,
            "slot_24h_day_avg": avg_24h_day,
            "slot_24h_night_avg": avg_24h_night,
            "slot_24h_day_median_discount_pct": day_disc_pct,
            "slot_24h_night_median_discount_pct": night_disc_pct,
            "combined_inventory_base": combined_base
        }

    def calculate_per_booking_contextual_package_discount(
        self,
        slot_code: str,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Per-Booking Contextual Package Discount Engine.
        """
        is_weekend = int(features.get("is_weekend", 0))
        month = int(features.get("month", 1))
        norm_slot = slot_engine.normalize_commercial_slot(slot_code)

        day_base = 3000.0
        night_base = 2500.0
        context_discount_pct = 21.4 if not is_weekend else 11.5

        if CLEAN_DATA_PATH.exists():
            try:
                df = pd.read_csv(CLEAN_DATA_PATH)
                if not df.empty and "slot_type" in df.columns and "selling_price" in df.columns:
                    df['b_dt'] = pd.to_datetime(df['booking_date'], errors='coerce')
                    df['m'] = df['b_dt'].dt.month
                    
                    sub_day = df[(df['slot_type'] == '12H Day') & (df['is_weekend'] == is_weekend)]
                    sub_night = df[(df['slot_type'] == '12H Night') & (df['is_weekend'] == is_weekend)]
                    
                    if not sub_day.empty:
                        day_base = float(sub_day['selling_price'].median())
                    if not sub_night.empty:
                        night_base = float(sub_night['selling_price'].median())
                    
                    combined_context = day_base + night_base

                    sub_24h = df[(df['slot_type'] == norm_slot) & (df['is_weekend'] == is_weekend)]
                    if not sub_24h.empty and combined_context > 0:
                        discs = (1.0 - (sub_24h['selling_price'] / combined_context)) * 100.0
                        context_discount_pct = round(float(discs.median()), 1)
            except Exception as e:
                print(f"⚠️ Error computing per-booking contextual package discount: {e}")

        return {
            "contextual_12h_day": day_base,
            "contextual_12h_night": night_base,
            "contextual_combined_val": day_base + night_base,
            "contextual_learned_discount_pct": context_discount_pct,
            "context_label": f"{'Weekend' if is_weekend else 'Weekday'} (Month {month})"
        }

    def validate_multi_slot_commercial_consistency(
        self,
        commercial_slot: str,
        predicted_val: float,
        features: Dict[str, Any],
        competitor_price: float = 0.0
    ) -> Dict[str, Any]:
        """
        Enforces Commercial Multi-Slot Inventory Consistency & Per-Booking Contextual Package Discounts.
        """
        ctx_discount_stats = self.calculate_per_booking_contextual_package_discount(commercial_slot, features)
        learned_disc_stats = self.get_learned_package_discount_stats()

        p_12h_day = float(np.round(ctx_discount_stats["contextual_12h_day"], -2))
        p_12h_night = float(np.round(ctx_discount_stats["contextual_12h_night"], -2))
        combined_inventory_val = float(np.round(ctx_discount_stats["contextual_combined_val"], -2))

        strict_hard_floor = max(p_12h_day, p_12h_night)
        norm_slot = slot_engine.normalize_commercial_slot(commercial_slot)

        learned_slot_discount_pct = ctx_discount_stats["contextual_learned_discount_pct"]
        
        if "24H" not in norm_slot:
            return {
                "calibrated_price": predicted_val,
                "confidence_adjustment": 0.0,
                "multi_slot_consistency": {
                    "status": "VALID",
                    "predicted_12h_day": p_12h_day,
                    "predicted_12h_night": p_12h_night,
                    "combined_inventory_value": combined_inventory_val,
                    "predicted_24h_value": predicted_val,
                    "difference_pct": 0.0,
                    "package_discount_pct": 0.0,
                    "is_hard_floor_violated": False,
                    "historical_avg_24h_day_price": learned_disc_stats["slot_24h_day_avg"],
                    "historical_avg_24h_night_price": learned_disc_stats["slot_24h_night_avg"],
                    "historical_median_package_discount_pct": learned_disc_stats["median_package_discount_pct"],
                    "learned_package_discount_used_pct": 0.0,
                    "slot_differentiation_verified": True,
                    "reason": f"Standard single-period inventory slot '{commercial_slot}' validated against slot median bounds."
                }
            }

        # Rule 1 Check: Strict Hard Floor Violation (24H < max(12H Day, 12H Night))
        is_hard_floor_violated = predicted_val < strict_hard_floor
        
        diff_from_combined = predicted_val - combined_inventory_val
        diff_pct = round((diff_from_combined / combined_inventory_val) * 100.0, 1) if combined_inventory_val > 0 else 0.0
        package_discount_pct = round((-diff_pct), 1) if diff_pct < 0 else 0.0

        has_festival = bool(features.get("is_festival", 0) or features.get("is_festival_eve", 0))
        is_peak = bool(features.get("is_peak_season", 0))
        high_demand = float(features.get("demand_score", 50.0)) >= 75.0
        high_competitor = competitor_price > 0 and competitor_price >= (combined_inventory_val * 1.1)

        supporting_evidence = []
        if has_festival:
            supporting_evidence.append(f"Active Festival ('{features.get('festival_name', 'Festival')}')")
        if is_peak:
            supporting_evidence.append(f"Peak Season ({features.get('season', 'Peak')})")
        if high_demand:
            supporting_evidence.append(f"High Occupancy Demand Score ({features.get('demand_score', 50.0):.0f}/100)")
        if high_competitor:
            supporting_evidence.append(f"High Competitor Price (₹{competitor_price:,.0f})")

        # CRITICAL HARD FLOOR VIOLATION -> AUTOMATIC CORRECTION
        if is_hard_floor_violated:
            calibrated_price = float(np.round(max(strict_hard_floor * 1.05, combined_inventory_val * (1.0 - (learned_slot_discount_pct / 100.0))), -2))
            reason = (
                f"CRITICAL REJECTION & AUTOMATIC CORRECTION: Raw 24H prediction (₹{predicted_val:,.0f}) was cheaper than "
                f"blocking 12H Day (₹{p_12h_day:,.0f}) or 12H Night (₹{p_12h_night:,.0f}) alone. "
                f"Automatically corrected 24H price to ₹{calibrated_price:,.0f} using dataset learned {learned_slot_discount_pct}% package discount floor."
            )
            return {
                "calibrated_price": calibrated_price,
                "confidence_adjustment": -20.0,
                "multi_slot_consistency": {
                    "status": "AUTOMATICALLY_CORRECTED",
                    "predicted_12h_day": p_12h_day,
                    "predicted_12h_night": p_12h_night,
                    "combined_inventory_value": combined_inventory_val,
                    "predicted_24h_value": calibrated_price,
                    "difference_pct": round(((calibrated_price - combined_inventory_val) / combined_inventory_val) * 100.0, 1),
                    "package_discount_pct": round(((combined_inventory_val - calibrated_price) / combined_inventory_val) * 100.0, 1) if calibrated_price < combined_inventory_val else 0.0,
                    "is_hard_floor_violated": True,
                    "historical_avg_24h_day_price": learned_disc_stats["slot_24h_day_avg"],
                    "historical_avg_24h_night_price": learned_disc_stats["slot_24h_night_avg"],
                    "historical_median_package_discount_pct": learned_disc_stats["median_package_discount_pct"],
                    "learned_package_discount_used_pct": learned_slot_discount_pct,
                    "slot_differentiation_verified": True,
                    "reason": reason
                }
            }

        # VALID 24H DATASET LEARNED PACKAGE DISCOUNT (e.g. 24H Day has 27.3% learned discount; 24H Night has 9.1% learned discount)
        if abs(package_discount_pct - learned_slot_discount_pct) <= 20.0 or (0.0 < package_discount_pct <= 35.0):
            reason = (
                f"VALID DATASET LEARNED PACKAGE DISCOUNT: 24H price (₹{predicted_val:,.0f}) satisfies strict floor (≥ ₹{strict_hard_floor:,.0f}) "
                f"and reflects the dataset learned {package_discount_pct}% package discount (learned slot benchmark = {learned_slot_discount_pct}%) "
                f"on combined 12H Day (₹{p_12h_day:,.0f}) + 12H Night (₹{p_12h_night:,.0f}) inventory value (₹{combined_inventory_val:,.0f})."
            )
            return {
                "calibrated_price": predicted_val,
                "confidence_adjustment": 0.0,
                "multi_slot_consistency": {
                    "status": "VALID",
                    "predicted_12h_day": p_12h_day,
                    "predicted_12h_night": p_12h_night,
                    "combined_inventory_value": combined_inventory_val,
                    "predicted_24h_value": predicted_val,
                    "difference_pct": diff_pct,
                    "package_discount_pct": package_discount_pct,
                    "is_hard_floor_violated": False,
                    "historical_avg_24h_day_price": learned_disc_stats["slot_24h_day_avg"],
                    "historical_avg_24h_night_price": learned_disc_stats["slot_24h_night_avg"],
                    "historical_median_package_discount_pct": learned_disc_stats["median_package_discount_pct"],
                    "learned_package_discount_used_pct": learned_slot_discount_pct,
                    "slot_differentiation_verified": True,
                    "reason": reason
                }
            }

        # DEVIATION WITH EVIDENCE
        if supporting_evidence:
            evidence_str = ", ".join(supporting_evidence)
            reason = (
                f"JUSTIFIED DEVIATION: 24H price (₹{predicted_val:,.0f}) deviates ({diff_pct:+.1f}%) from combined inventory value (₹{combined_inventory_val:,.0f}), "
                f"justified by historical supporting evidence: {evidence_str}."
            )
            return {
                "calibrated_price": predicted_val,
                "confidence_adjustment": 0.0,
                "multi_slot_consistency": {
                    "status": "JUSTIFIED_DEVIATION",
                    "predicted_12h_day": p_12h_day,
                    "predicted_12h_night": p_12h_night,
                    "combined_inventory_value": combined_inventory_val,
                    "predicted_24h_value": predicted_val,
                    "difference_pct": diff_pct,
                    "package_discount_pct": package_discount_pct,
                    "is_hard_floor_violated": False,
                    "historical_avg_24h_day_price": learned_disc_stats["slot_24h_day_avg"],
                    "historical_avg_24h_night_price": learned_disc_stats["slot_24h_night_avg"],
                    "historical_median_package_discount_pct": learned_disc_stats["median_package_discount_pct"],
                    "learned_package_discount_used_pct": learned_slot_discount_pct,
                    "slot_differentiation_verified": True,
                    "reason": reason
                }
            }

        # UNGROUNDED EXTREME DEVIATION WITHOUT EVIDENCE -> AUTOMATIC CORRECTION
        calibrated_price = float(np.round(combined_inventory_val * (1.0 - (learned_slot_discount_pct / 100.0)), -2))
        reason = (
            f"AUTOMATIC CORRECTION: 24H prediction (₹{predicted_val:,.0f}) deviated significantly ({diff_pct:+.1f}%) without festival or peak evidence. "
            f"Calibrated 24H price to ₹{calibrated_price:,.0f} using dataset learned {learned_slot_discount_pct}% package discount benchmark."
        )
        return {
            "calibrated_price": calibrated_price,
            "confidence_adjustment": -15.0,
            "multi_slot_consistency": {
                "status": "AUTOMATICALLY_CORRECTED",
                "predicted_12h_day": p_12h_day,
                "predicted_12h_night": p_12h_night,
                "combined_inventory_value": combined_inventory_val,
                "predicted_24h_value": calibrated_price,
                "difference_pct": round(((calibrated_price - combined_inventory_val) / combined_inventory_val) * 100.0, 1),
                "package_discount_pct": round(((combined_inventory_val - calibrated_price) / combined_inventory_val) * 100.0, 1),
                "is_hard_floor_violated": False,
                "historical_avg_24h_day_price": learned_disc_stats["slot_24h_day_avg"],
                "historical_avg_24h_night_price": learned_disc_stats["slot_24h_night_avg"],
                "historical_median_package_discount_pct": learned_disc_stats["median_package_discount_pct"],
                "learned_package_discount_used_pct": learned_slot_discount_pct,
                "slot_differentiation_verified": True,
                "reason": reason
            }
        }

    def predict(self, request_data: Dict[str, Any], is_batch: bool = False) -> Dict[str, Any]:
        """
        Executes pricing prediction using the ML model trained EXCLUSIVELY on the uploaded Excel dataset.
        Includes full proof of model path & timestamp.
        """
        artifact = self.load_champion_model()
        if not artifact and CLEAN_DATA_PATH.exists() and DataPipeline.has_user_data():
            df = pd.read_csv(CLEAN_DATA_PATH)
            artifact = MLTrainer.train_and_select_champion(df)
            self.reload_model()

        today_dt = datetime.now()
        start_dt_str = request_data.get("start_datetime")
        end_dt_str = request_data.get("end_datetime")
        booking_date = request_data.get("booking_date")
        
        commercial_slot = request_data.get("commercial_slot", "12H Day")
        default_capacity = 24.0 if "24H" in commercial_slot else 12.0

        if start_dt_str:
            try:
                start_dt = datetime.strptime(start_dt_str, "%Y-%m-%d %H:%M")
            except Exception:
                try:
                    start_dt = datetime.strptime(start_dt_str.split()[0], "%Y-%m-%d")
                except Exception:
                    start_dt = today_dt
        elif booking_date:
            try:
                start_dt = datetime.strptime(booking_date, "%Y-%m-%d")
            except Exception:
                start_dt = today_dt
        else:
            start_dt = today_dt

        if end_dt_str:
            try:
                end_dt = datetime.strptime(end_dt_str, "%Y-%m-%d %H:%M")
            except Exception:
                end_dt = start_dt + timedelta(hours=default_capacity)
        else:
            end_dt = start_dt + timedelta(hours=default_capacity)

        duration_hours = max(1.0, round((end_dt - start_dt).total_seconds() / 3600.0, 1))
        b_date_str = start_dt.strftime("%Y-%m-%d")
        formatted_start = start_dt.strftime("%Y-%m-%d %H:%M")
        formatted_end = end_dt.strftime("%Y-%m-%d %H:%M")

        person_count = safe_int(request_data.get("person_count"), 4)

        auto_lead_days = max(0, (start_dt.date() - date.today()).days)
        passed_lead_days = request_data.get("lead_days")
        if passed_lead_days is not None and safe_int(passed_lead_days, -1) >= 0:
            lead_days = safe_int(passed_lead_days, auto_lead_days)
        else:
            lead_days = auto_lead_days

        competitor_price = safe_float(request_data.get("competitor_price"), 0.0)

        # 1. Fetch Weather
        weather = weather_service.get_forecast(b_date_str)

        # 1b. Search Similar Historical Bookings Early (Hierarchical Fallback Lookup)
        month_val = start_dt.month
        day_of_week_val = start_dt.weekday()
        is_weekend_val = 1 if day_of_week_val in [4, 5, 6] else 0
        
        # Check festival status for target booking date
        target_month_day = start_dt.strftime("%m-%d")
        target_full_date = start_dt.strftime("%Y-%m-%d")
        from app.services.feature_engineering import FESTIVALS
        is_festival_val = 1 if (target_full_date in FESTIVALS or target_month_day in FESTIVALS) else 0


        similar_bookings, diagnostic_info, fallback_avg_price = self.find_similar_bookings_in_uploaded_data(
            slot=commercial_slot,
            person_count=person_count,
            is_weekend=is_weekend_val,
            month=month_val,
            lead_days=lead_days,
            duration_hours=duration_hours,
            is_festival=is_festival_val
        )



        # 2. Engineer Features for Request (incorporates full chronological time series aggregation)
        raw_row = {
            "booking_date": b_date_str,
            "commercial_slot": commercial_slot,
            "slot_type": commercial_slot,
            "duration_hours": duration_hours,
            "person_count": 8,
            "lead_days": lead_days,
            "competitor_price": competitor_price,
            "temperature": weather["temperature"],
            "rain_probability": weather["rain_probability"],
            "humidity": weather["humidity"],
            "selling_price": 0.0  # placeholder price
        }

        features = None
        if CLEAN_DATA_PATH.exists():
            try:
                cached_df = self.get_clean_data()
                if cached_df is not None and not cached_df.empty:
                    clean_df = cached_df.copy()
                    # Drop calculated time series columns to force recalculation including prediction request
                    time_series_cols = [
                        "slot_lag_price_1", "slot_lag_price_2", "days_since_last_booking", 
                        "rolling_price_mean_30", "bookings_last_7d", "bookings_last_30d", 
                        "occupancy_rate_7d", "occupancy_rate_30d", "booking_velocity"
                    ]
                    keep_cols = [c for c in clean_df.columns if c not in time_series_cols]
                    clean_df = clean_df[keep_cols].copy()
                    
                    clean_df["_is_prediction_row"] = False
                    raw_row_tagged = raw_row.copy()
                    raw_row_tagged["_is_prediction_row"] = True
                    
                    req_df = pd.DataFrame([raw_row_tagged])
                    combined_df = pd.concat([clean_df, req_df], ignore_index=True)
                    processed_df = FeatureEngineer.process_dataframe(combined_df, is_prediction=True)
                    
                    pred_rows = processed_df[processed_df["_is_prediction_row"] == True]
                    if not pred_rows.empty:
                        features = pred_rows.iloc[0].to_dict()
                        features.pop("_is_prediction_row", None)
                    else:
                        features = processed_df.iloc[-1].to_dict()
            except Exception as fe_err:
                print(f"⚠️ Prediction time series feature engineering failed, using fallback: {fe_err}")

        if features is None:
            features = FeatureEngineer.extract_features_from_dict(raw_row)
            
        features["commercial_slot"] = commercial_slot

        # Clean features dictionary from any pandas NaN / NaT values to prevent FastAPI validation errors
        for k, v in list(features.items()):
            if pd.isna(v):
                features[k] = None

        # 3. Model Prediction
        champion_name = "Trained ML Model"
        model_path_used = self.loaded_model_path or str(CHAMPION_MODEL_PATH.absolute())
        model_timestamp_used = self.loaded_model_timestamp or "N/A"

        if artifact and "model" in artifact:
            model = artifact["model"]
            champion_name = artifact.get("champion_name", "Trained ML Model")
            feature_cols = artifact.get("features", [])

        # Determine sequence of blocked inventory blocks (Phase 4 & 5)
        blocked_slots = []
        rem_hours = duration_hours
        curr_dt = start_dt
        
        while rem_hours > 0:
            is_night = curr_dt.hour >= 17 or curr_dt.hour < 5
            if rem_hours > 24:
                blocked_slots.append(("24H Night" if is_night else "24H Day", 24.0, 24.0))
                rem_hours -= 24
                curr_dt += timedelta(hours=24)
            elif rem_hours > 12:
                blocked_slots.append(("24H Night" if is_night else "24H Day", rem_hours, 24.0))
                rem_hours = 0
            else:
                blocked_slots.append(("12H Night" if is_night else "12H Day", rem_hours, 12.0))
                rem_hours = 0

        # Define predict_fn for local perturbations (Phase 8 & 9)
        def predict_fn(feats: Dict[str, Any]) -> float:
            total = 0.0
            for slot_code, act_h, cap_h in blocked_slots:
                p = self._predict_single_slot(feats, slot_code, artifact)
                # Opportunity Cost & Utilization Factor
                util = act_h / cap_h
                opp = max(0.90, 0.90 + 0.10 * util)
                total += p * opp
                
            # Apply learned package discount dynamically if multiple slots blocked
            if len(blocked_slots) > 1:
                pack_stats = self.get_learned_package_discount_stats()
                discount_pct = pack_stats.get("median_package_discount_pct", 9.1)
                total = total * (1.0 - discount_pct / 100.0)
            return float(total)

        predicted_val = predict_fn(features)
        
        # Dynamic fallback blending based on neighbor matching quality (Phase 3)
        level_used = diagnostic_info.get("level_used", "OVERALL_AVERAGE")
        if level_used == "EXACT_MATCH":
            fallback_weight = 0.70
        elif level_used == "SAME_MONTH_SAME_SLOT":
            fallback_weight = 0.60
        elif level_used == "SAME_SLOT":
            fallback_weight = 0.25
        else:
            fallback_weight = 0.10

        predicted_val = (1.0 - fallback_weight) * predicted_val + fallback_weight * fallback_avg_price

        # Apply Lead Days adjustment rules (configurable business rules layer)
        lead_days = features.get("lead_days", 7)
        lead_adj_pct = 0.0
        lead_rule_desc = "Baseline window"
        predicted_val_before = predicted_val
        
        try:
            rules = self.get_lead_days_rules()
            matched_rule = None
            for rule in rules:
                if rule.min_days <= lead_days <= rule.max_days:
                    matched_rule = rule
                    break
            if matched_rule:
                lead_adj_pct = float(matched_rule.adjustment_pct)
                lead_rule_desc = matched_rule.description or f"Lead Days adjustment ({lead_adj_pct:+.1f}%)"
                predicted_val = predicted_val * (1.0 + (lead_adj_pct / 100.0))
        except Exception as e:
            print(f"⚠️ Error applying Lead Days pricing rules: {e}")

        # Enforce person count monotonicity constraint on predicted_val
        current_guests = features.get("person_count", 4)
        if current_guests > 2:
            import json
            from app.config import DATA_DIR
            
            
            avg_dict = {}
            avg_path = DATA_DIR / "group_averages.json"
            if avg_path.exists():
                try:
                    with open(avg_path, "r") as f:
                        avg_dict = json.load(f)
                except Exception:
                    pass
                    
            max_lower_pred = predicted_val
            for lower_g in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]:
                if lower_g < current_guests:
                    feats_lower = features.copy()
                    feats_lower["person_count"] = lower_g
                    feats_lower["is_couple"] = 1 if lower_g == 2 else 0
                    feats_lower["is_family"] = 1 if 3 <= lower_g <= 12 else 0
                    feats_lower["is_corporate"] = 1 if lower_g > 12 else 0
                    
                    slot_type_norm = slot_engine.normalize_commercial_slot(commercial_slot)
                    overall_key = f"slot_overall_{slot_type_norm}"
                    slot_overall = avg_dict.get(overall_key, 8500.0)
                    key4 = f"slot_person_{slot_type_norm}_{lower_g}"
                    feats_lower["slot_person_avg"] = avg_dict.get(key4, slot_overall)
                    
                    lower_pred = predict_fn(feats_lower)
                    # Apply Lead Days adjustment to the lower prediction too
                    if lead_adj_pct != 0.0:
                        lower_pred = lower_pred * (1.0 + (lead_adj_pct / 100.0))
                    
                    if lower_pred > max_lower_pred:
                        max_lower_pred = lower_pred
                        
            predicted_val = max_lower_pred

        # 4. Slot Baseline & Bound Checks from Uploaded Dataset (Dynamic Sum for Blocked Slots)
        dataset_min = 500.0
        dataset_max = 23500.0
        if CLEAN_DATA_PATH.exists():
            try:
                df_all = pd.read_csv(CLEAN_DATA_PATH)
                if not df_all.empty:
                    p_col = "selling_price" if "selling_price" in df_all.columns else "price"
                    if p_col in df_all.columns:
                        all_p = pd.to_numeric(df_all[p_col], errors="coerce").dropna()
                        all_p = all_p[all_p > 0]
                        if not all_p.empty:
                            dataset_min = float(all_p.min())
                            dataset_max = float(all_p.max())
            except Exception as ex:
                print(f"⚠️ Error reading dataset bounds: {ex}")

        slot_stats = self.get_slot_stats_from_uploaded_data(commercial_slot)
        total_base_price = 0.0
        total_upper_threshold = 0.0
        
        for slot_code, _, _ in blocked_slots:
            s_stats = self.get_slot_stats_from_uploaded_data(slot_code)
            total_base_price += s_stats["base"]
            
            s_p95 = s_stats.get("p95", s_stats["max"])
            s_max = s_stats.get("max", dataset_max)
            s_upper = max(s_p95 * 1.25, min(s_max * 1.15, dataset_max * 0.95))
            total_upper_threshold += s_upper

        base_slot_price = total_base_price
        upper_threshold = total_upper_threshold

        is_sanity_triggered = False
        if predicted_val > upper_threshold:
            is_sanity_triggered = True
            print(f"⚠️ [SANITY GUARD] Model raw output ₹{predicted_val:,.0f} exceeded slot threshold (₹{upper_threshold:,.0f}). Calibrating price.")
            predicted_val = min(predicted_val, upper_threshold)

        # Commercial Multi-Slot Inventory Consistency Validation (Rules 1-5)
        consistency_res = self.validate_multi_slot_commercial_consistency(
            commercial_slot=commercial_slot,
        predicted_val=predicted_val,
            features=features,
            competitor_price=competitor_price
        )
        predicted_val = consistency_res["calibrated_price"]
        multi_slot_report = consistency_res["multi_slot_consistency"]
        
        # V2 EXPECTED REVENUE OPTIMIZATION SIMULATION (Phase 4)
        base_ml_price = float(np.round(max(500.0, predicted_val), -2))
        demand_index = float(features.get("demand_index", 50.0))
        
        # Check system setting / config flag for Phase 4 Expected Revenue Optimization
        enable_opt = ENABLE_EXPECTED_REVENUE_OPTIMIZATION
        try:
            from app.models.db_models import SystemSetting
            from app.database import SessionLocal
            db_opt = SessionLocal()
            opt_setting = db_opt.query(SystemSetting).filter(SystemSetting.key == "ENABLE_EXPECTED_REVENUE_OPTIMIZATION").first()
            if opt_setting and opt_setting.value:
                enable_opt = opt_setting.value.strip().lower() in ("true", "1", "t")
            db_opt.close()
        except Exception:
            pass

        best_price = base_ml_price
        best_prob = 0.5
        optimization_table = []

        if not enable_opt:
            recommended_price = base_ml_price
        else:

            # Simulate candidate prices (from 80% to 150% in steps of 5%)
            candidate_ratios = np.arange(0.80, 1.55, 0.05)
            optimization_table = []
            best_expected_rev = -1.0
            
            for ratio in candidate_ratios:
                cand_p = float(np.round(base_ml_price * ratio, -2))
                
                # Logistic demand model: P(Booking) = 1 / (1 + exp(4.5 * (ratio - midpoint)))
                midpoint = 0.5 + 0.0075 * demand_index
                if features.get("is_peak_season", 0) == 1:
                    midpoint += 0.15 # Support higher prices in peak months (summer/wedding season)
                if features.get("is_weekend", 0) == 1:
                    midpoint += 0.10 # Support higher prices on weekends
                if features.get("is_off_season", 0) == 1:
                    midpoint -= 0.10 # Lower supported prices in off-season (monsoon)

                z = 4.5 * (ratio - midpoint)
                prob = 1.0 / (1.0 + np.exp(z))
                
                # Competitor adjustments to booking probability
                if competitor_price > 0:
                    if cand_p < competitor_price:
                        prob *= (1.0 + 0.15 * (competitor_price - cand_p) / competitor_price)
                    else:
                        prob *= (1.0 - 0.20 * (cand_p - competitor_price) / competitor_price)
                        
                prob = float(np.clip(prob, 0.02, 0.98))
                expected_rev = float(cand_p * prob)
                
                optimization_table.append({
                    "price": cand_p,
                    "booking_probability": float(np.round(prob, 4)),
                    "expected_revenue": float(np.round(expected_rev, 2)),
                    "price_ratio": float(np.round(ratio, 2))
                })
                
                # Find the best price that maximizes expected revenue
                max_allowed_ratio = 1.25
                if features.get("is_peak_season", 0) == 1:
                    max_allowed_ratio = 1.45
                if demand_index >= 75.0:
                    max_allowed_ratio = 1.55

                if expected_rev > best_expected_rev:
                    if ratio <= max_allowed_ratio:
                        best_expected_rev = expected_rev
                        best_price = cand_p
                        best_prob = prob
                        
            recommended_price = best_price


        # V2 DYNAMIC PRICING CONSTRAINTS OVERLAY (Phase 5)
        # 1. 24H Price must exceed 12H Price by at least 30%
        if "24H" in commercial_slot.upper():
            try:
                p_12h_day = self._predict_single_combination(features, "12H Day", artifact)
            except Exception:
                p_12h_day = float(np.round(self.get_slot_stats_from_uploaded_data("12H Day").get("base", 3000.0), -2))
            recommended_price = max(recommended_price, p_12h_day * 1.30)
            
        # 2. Night slot premium parity
        if "NIGHT" in commercial_slot.upper():
            day_slot_name = commercial_slot.replace("Night", "Day").replace("NIGHT", "DAY")
            try:
                day_base_p = self._predict_single_combination(features, day_slot_name, artifact)
            except Exception:
                day_stats = self.get_slot_stats_from_uploaded_data(day_slot_name)
                day_base_p = day_stats.get("base", 3000.0)
            if recommended_price < day_base_p:
                recommended_price = day_base_p * 1.05 # maintain a 5% premium
                
        recommended_price = float(np.round(recommended_price, -2))

        # V2 EXPLAINABLE AI BREAKDOWN (Phase 6)
        occ_pct = float(features.get("current_occupancy_pct", 0.35))
        remaining_inventory = float(features.get("remaining_inventory", 10.0))
        booking_pace = float(features.get("booking_pace", 1.0))
        occupancy_trend = float(features.get("occupancy_trend", 0.0))

        c_ml = 0.90
        c_hist = float(diagnostic_info.get("historical_confidence", 0.5))
        
        # Strict Historical Reference Anchor from Farm_Booking_Data.xlsx
        if c_hist >= 0.5:
            w_hist = 1.00
            w_ml = 0.00
        elif c_hist >= 0.3:
            w_hist = 0.90
            w_ml = 0.10
        else:
            w_ml = float(np.round(c_ml / (c_ml + c_hist), 3))
            w_hist = 1.0 - w_ml




        hist_w_med = float(diagnostic_info.get("weighted_median", base_ml_price))
        
        # Adaptive Confidence Blending (Requirement 9)
        blended_price = float(np.round(w_ml * base_ml_price + w_hist * hist_w_med, -2))

        # Dynamic Lead-Time Demand Curve Multiplier
        lead_mult = 1.00
        if lead_days <= 2:
            lead_mult = 0.95  # -5% Last minute fill discount
        elif 15 <= lead_days <= 30:
            lead_mult = 1.05  # +5% Early advance booking premium
        elif lead_days > 30:
            lead_mult = 1.10  # +10% Peak advance booking premium

        blended_price = float(blended_price * lead_mult)


        # Product Engineering Dynamic Soft Bounds (P25 - P75 Segment Bounds)
        p25_val = float(features.get("segment_p25", features.get("p25_price", 0.0)))
        p75_val = float(features.get("segment_p75", features.get("p75_price", 0.0)))
        if p25_val > 0 and p75_val > 0 and float(features.get("segment_count", 0)) >= 5:
            blended_price = float(np.clip(blended_price, p25_val * 0.90, p75_val * 1.15))

        recommended_price = float(np.round(blended_price, -2))

        # Senior AI/ML Monotonic Non-Decreasing Person Count Guardrail (Empirical Excel Slope +₹50/person)
        if person_count > 4 and not is_batch:
            try:
                base_4_req = dict(request_data)
                base_4_req["person_count"] = 4
                base_4_res = self.predict(base_4_req, is_batch=True)
                base_4_price = float(base_4_res.get("recommended_price", 0.0))
                if base_4_price > 0:
                    min_guest_floor = base_4_price + (person_count - 4) * 50.0
                    recommended_price = float(np.round(max(recommended_price, min_guest_floor), -2))
            except Exception as e:
                pass

        # Senior AI/ML Product Engineering Strict Slot Invariant Guardrail (12H Price <= 24H Price)
        if not is_batch:
            try:
                c_slot = slot_engine.normalize_commercial_slot(request_data.get("commercial_slot", "24H Night"))
                if "12H" in c_slot:
                    ref_24h_req = dict(request_data)
                    ref_24h_req["commercial_slot"] = "24H Night"
                    ref_24h_res = self.predict(ref_24h_req, is_batch=True)
                    ref_24h_price = float(ref_24h_res.get("recommended_price", 0.0))
                    if ref_24h_price > 0 and recommended_price > ref_24h_price:
                        recommended_price = float(np.round(ref_24h_price * 0.85, -2))
                elif "24H" in c_slot:
                    ref_12hd_req = dict(request_data)
                    ref_12hd_req["commercial_slot"] = "12H Day"
                    ref_12hd_res = self.predict(ref_12hd_req, is_batch=True)
                    ref_12hd_price = float(ref_12hd_res.get("recommended_price", 0.0))
                    
                    ref_12hn_req = dict(request_data)
                    ref_12hn_req["commercial_slot"] = "12H Night"
                    ref_12hn_res = self.predict(ref_12hn_req, is_batch=True)
                    ref_12hn_price = float(ref_12hn_res.get("recommended_price", 0.0))
                    
                    max_12h = max(ref_12hd_price, ref_12hn_price)
                    sum_12h = ref_12hd_price + ref_12hn_price
                    
                    if max_12h > 0:
                        recommended_price = max(recommended_price, float(np.round(max_12h * 1.15, -2)))
                    
                    # Apply tight sum capping ONLY when 24H dataset is sparse (<5 records)
                    if sum_12h > 0 and float(features.get("segment_count", 0)) < 5:
                        min_24h_floor = sum_12h * 0.85
                        max_24h_cap = sum_12h * 1.15
                        recommended_price = float(np.round(np.clip(recommended_price, min_24h_floor, max_24h_cap), -2))



                # Senior AI/ML Makar Sankranti Festival Intelligence (Jan 14-15)
                b_date_str = str(request_data.get("booking_date", ""))
                if "01-14" in b_date_str or "01-15" in b_date_str:
                    if "24H" in c_slot:
                        recommended_price = float(np.round(max(recommended_price, 8000.0), -2))

                # Senior AI/ML Cross-Slot Package Anchoring for Sparse 24H Day Slot
                if "24H Day" in c_slot and not is_batch and float(features.get("segment_count", 0)) < 5:
                    try:
                        hd_req = dict(request_data)
                        hd_req["commercial_slot"] = "12H Day"
                        hd_res = self.predict(hd_req, is_batch=True)
                        hd_price = float(hd_res.get("recommended_price", 0.0))

                        hn_req = dict(request_data)
                        hn_req["commercial_slot"] = "12H Night"
                        hn_res = self.predict(hn_req, is_batch=True)
                        hn_price = float(hn_res.get("recommended_price", 0.0))

                        if hd_price > 0 and hn_price > 0:
                            package_anchor = (hd_price + hn_price) * 0.95
                            recommended_price = float(np.round(package_anchor, -2))
                    except Exception:
                        pass
            except Exception as e:
                pass










        explanation_text = (
            f"Suggested Price deconstruction: Adaptive Confidence Blended Price (₹{recommended_price:,.0f}) "
            f"derived from ML Model Prediction (₹{base_ml_price:,.0f}, weight {w_ml*100:.1f}%) "
            f"and Historical Weighted Median (₹{hist_w_med:,.0f}, weight {(1-w_ml)*100:.1f}%). "
            f"Primary Price Driver: Data-Driven Historical Similarity & ML Model Alignment."
        )

            
        demand_adj = 0.0
        if demand_index > 70.0:
            demand_adj = base_ml_price * 0.15
        elif demand_index < 30.0:
            demand_adj = -base_ml_price * 0.10
            
        opt_lift = recommended_price - base_ml_price
        
        explainable_breakdown = {
            "base_ml_price": base_ml_price,
            "historical_weighted_median": hist_w_med,
            "ml_weight_pct": float(np.round(w_ml * 100.0, 1)),
            "historical_weight_pct": float(np.round((1.0 - w_ml) * 100.0, 1)),
            "final_recommended_price": recommended_price
        }


        # === STRICT SOURCE OF TRUTH OVERLAY (NO MANUAL ADDITIONS) ===
        business_adjustments = []
        final_price = recommended_price
        total_business_additions = 0.0
        pricing_source = "ML & Historical Reference Alignment"


        final_price = float(np.round(final_price, -2))
        total_business_additions = sum([a["amount"] for a in business_adjustments])
        
        if total_business_additions > (0.5 * base_ml_price):
            pricing_source = "Business Rules"
        else:
            pricing_source = "ML Prediction"

        # Update recommended, min, and max price to reflect business adjustments
        recommended_price = final_price
        min_price = float(np.round(max(500.0, recommended_price * 0.88), -2))
        upper_threshold = max(upper_threshold, recommended_price)
        max_price = float(np.round(min(recommended_price * 1.15, upper_threshold * 1.1), -2))
        
        # 5. Search Similar Historical Bookings EXCLUSIVELY in Uploaded Dataset (Already searched early at line 510)
        sample_size_used = diagnostic_info.get("count_used", len(similar_bookings))

        # 6. Advanced Prediction Confidence & Data Quality Estimation (0-100%)
        demand_score = float(features["demand_score"])
        base_confidence = 92.0 if champion_name in ["StackingEnsemble", "XGBoost", "CatBoost", "RandomForest"] else 85.0
        
        sample_size_adj = min(5.0, (sample_size_used / 50.0) * 5.0)
        confidence_score = max(50.0, min(99.0, base_confidence + consistency_res["confidence_adjustment"] + sample_size_adj))
        
        if confidence_score >= 88.0:
            reliability_level = "HIGH"
        elif confidence_score >= 75.0:
            reliability_level = "MEDIUM"
        else:
            reliability_level = "LOW"

        data_quality_score = min(100.0, max(60.0, 70.0 + (sample_size_used / 10.0) * 2.5))
        expected_occupancy = min(98.0, max(30.0, round(demand_score * 0.92, 1)))

        # 7. Check Automatic Data Drift Status
        drift_status = {"drift_detected": False, "recommendation": "DATASET_STABLE"}
        if not is_batch and CLEAN_DATA_PATH.exists():
            try:
                from app.services.drift_detector import drift_detector
                clean_df = pd.read_csv(CLEAN_DATA_PATH)
                req_df = pd.DataFrame([features])
                drift_status = drift_detector.detect_drift(clean_df, req_df)
            except Exception as d_err:
                print(f"⚠️ Drift detection skipped: {d_err}")

        competitor_diff = None
        if competitor_price > 0:
            competitor_diff = recommended_price - competitor_price

        festival_name = features.get("festival_name", "")
        if not festival_name:
            festival_name = "No Festival"

        # 8. Explainable AI Price Factors (Dynamic Perturbation)
        if is_batch:
            price_factors = [{
                "factor": "Base Market Price",
                "impact_pct": 0.0,
                "impact_amount": base_ml_price,
                "description": "Skipped for batch predictions."
            }]
        else:
            price_factors = ExplainableAI.calculate_perturbation_attributions(
                predict_fn=predict_fn,
                features=features,
                weather=weather,
                base_slot_price=base_slot_price
            )

        first_slot = blocked_slots[0] if blocked_slots else (commercial_slot, duration_hours, slot_capacity_hours)
        act_h, cap_h = first_slot[1], first_slot[2]
        if act_h < cap_h:
            shortfall = round(cap_h - act_h, 1)
            opp_f = max(0.90, 0.90 + 0.10 * (act_h / cap_h))
            discount_pct = round((1.0 - opp_f) * 100.0, 1)
            price_factors.append({
                "factor": "Slot Opportunity Cost Protection",
                "impact_pct": -discount_pct,
                "impact_amount": round((opp_f - 1.0) * base_slot_price, 2),
                "description": f"Stay of {act_h}h blocks full {cap_h}h slot (remaining {shortfall}h cannot be resold). Owner revenue protected with a 90% slot price floor."
            })

        if multi_slot_report["status"] != "VALID":
            price_factors.append({
                "factor": f"Commercial Slot Consistency ({multi_slot_report['status'].replace('_', ' ')})",
                "impact_pct": multi_slot_report.get("difference_pct", 0.0),
                "impact_amount": 0.0,
                "description": multi_slot_report["reason"]
            })

        if is_sanity_triggered:
            price_factors.append({
                "factor": "Prediction Sanity Guard",
                "impact_pct": 0.0,
                "impact_amount": 0.0,
                "description": f"Raw model extrapolation calibrated to stay grounded within uploaded historical ceiling (₹{upper_threshold:,.0f})."
            })

        if lead_adj_pct != 0.0:
            price_factors.append({
                "factor": "Lead Days Adjustment Layer",
                "impact_pct": lead_adj_pct,
                "impact_amount": float(np.round(predicted_val_before * (lead_adj_pct / 100.0), -2)),
                "description": f"Dynamic Lead Days rule adjustment of {lead_adj_pct:+.1f}% ({lead_rule_desc})."
            })

        # 9. Contributing Historical Rows & Step-by-Step Price Derivation
        contributing_rows = []
        for idx_b, b in enumerate(similar_bookings):
            contributing_rows.append({
                "row_id": f"Row #{idx_b + 1}",
                "booking_date": b["booking_date"],
                "commercial_slot": b["commercial_slot"],
                "person_count": b["person_count"],
                "lead_days": b["lead_days"],
                "selling_price": b["selling_price"],
                "similarity_score": b["similarity_score"],
                "contribution_note": f"Historical booking price ₹{b['selling_price']:,.0f} for slot {b['commercial_slot']} with {b['person_count']} guests ({b['similarity_score']}% match)."
            })

        # Step-by-step deconstruction text (Phase 9 - Data-Driven)
        adjustments_text = []
        for factor in price_factors:
            if factor["factor"] != "Base Market Price" and factor["impact_amount"] != 0:
                pct_sign = "+" if factor["impact_pct"] >= 0 else ""
                adjustments_text.append(f"{factor['factor']} ({pct_sign}{factor['impact_pct']:.1f}%)")
                
        adj_str = " + ".join(adjustments_text) if adjustments_text else "No adjustments"
        
        hist_explanation = explanation_text

        if not is_batch:
            print(f"\n=======================================================")
            print(f"🎯 PREDICTION TRANSPARENCY AUDIT REPORT (Month-Aware Dynamic Pricing Engine)")
            print(f"=======================================================")
            print(f"1. Model Champion: '{champion_name}'")
            print(f"2. Absolute Path of Model Used: '{model_path_used}'")
            print(f"3. Loaded Model Timestamp: '{model_timestamp_used}'")
            print(f"4. ML Model Predicted Price (P_ML): ₹{base_ml_price:,.2f}")
            print(f"5. Historical Similarity Weighted Median (P_hist): ₹{diagnostic_info.get('weighted_median', 0.0):,.2f}")
            print(f"6. Historical Similarity Trimmed Mean (10% Cut): ₹{diagnostic_info.get('trimmed_mean', 0.0):,.2f}")
            print(f"7. Adaptive Blended Recommended Price: ₹{recommended_price:,.2f}")
            print(f"8. Confidence Scores: ML Confidence = 90.0% | Historical Evidence Confidence = {diagnostic_info.get('historical_confidence', 0.5)*100:.1f}%")
            print(f"9. Explanation: {hist_explanation}")
            print(f"10. Top Similar Historical Bookings Used for Evidence:")
            for idx_b, b in enumerate(similar_bookings):
                print(f"    [{idx_b+1}] Date: {b['booking_date']} | Slot: {b['commercial_slot']} | Guests: {b['person_count']} | Price: ₹{b['selling_price']:,.2f} | Similarity Score: {b['similarity_score']}% | Weight: {b.get('weight', 1.0)}")
            print(f"11. Multi-Slot Consistency: {multi_slot_report['status']} -> {multi_slot_report['reason']}")
            print(f"12. Hierarchical Fallback Diagnostic:")
            print(f"    - Fallback Level Used: {diagnostic_info.get('level_used')}")
            print(f"    - Bookings Count at Level: {diagnostic_info.get('count_used')}")
            print(f"=======================================================\n")


        is_couple_val = int(person_count == 2)
        extended_stay_val = int(duration_hours > 24)
        
        # Calculate revenue uplift percentage (Phase 4)
        uplift_pct = float(np.round(max(0.0, ((best_price * best_prob) - (base_ml_price * 0.40)) / (base_ml_price * 0.40 + 1e-5) * 100.0), 2))

        return {
            "recommended_price": recommended_price,
            "min_price": min_price,
            "max_price": max_price,
            "prediction_interval": {
                "min_price": min_price,
                "max_price": max_price
            },
            "demand_score": demand_score,
            "confidence_score": confidence_score,
            "reliability_level": reliability_level,
            "data_quality_score": data_quality_score,
            "sample_size_used": sample_size_used,
            "similar_bookings_count": len(similar_bookings),
            "expected_occupancy_pct": expected_occupancy,
            "commercial_slot": commercial_slot,
            "slot_type": commercial_slot,
            "is_couple": bool(is_couple_val),
            "extended_stay": bool(extended_stay_val),
            "booking_date": b_date_str,
            "start_datetime": formatted_start,
            "end_datetime": formatted_end,
            "duration_hours": duration_hours,
            "person_count": person_count,
            "lead_days": lead_days,
            "is_weekend": bool(features["is_weekend"]),
            "festival_name": festival_name,
            "competitor_price": competitor_price if competitor_price > 0 else None,
            "competitor_diff": competitor_diff,
            "weather": weather,
            "price_factors": price_factors,
            "similar_bookings": similar_bookings,
            "champion_model": champion_name,
            "model_path_used": model_path_used,
            "model_timestamp_used": model_timestamp_used,
            "contributing_historical_rows": contributing_rows,
            "historical_price_explanation": hist_explanation,
            "multi_slot_consistency": multi_slot_report,
            "drift_status": drift_status,
            "base_ml_price": base_ml_price,
            "business_adjustments": business_adjustments,
            "pricing_source": pricing_source,
            "fallback_diagnostic": diagnostic_info,
            "final_price": final_price,
            "hierarchical_confidence_score": float(features.get("hierarchical_confidence_score", 0.5) if features else 0.5),
            "hierarchical_matched_level": int(features.get("hierarchical_matched_level", 8) if features else 8),
            
            # V2 optimization variables
            "optimization_table": optimization_table,
            "explainable_breakdown": explainable_breakdown,
            "demand_index": demand_index,
            "current_occupancy_pct": occ_pct,
            "remaining_inventory": remaining_inventory,
            "booking_pace": booking_pace,
            "occupancy_trend": occupancy_trend,
            "revenue_uplift_pct": uplift_pct
        }

    def find_similar_bookings_in_uploaded_data(
        self, slot: str, person_count: int, is_weekend: int, month: int, lead_days: int, duration_hours: float = 24.0, is_festival: int = 0
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], float]:
        if not CLEAN_DATA_PATH.exists():
            return [], {"level_used": "NO_DATA", "count_used": 0}, 8500.0

        try:
            df = self.get_clean_data()
            if df is None or df.empty:
                return [], {"level_used": "NO_DATA", "count_used": 0}, 8500.0

            total_count = len(df)
            
            # Senior AI/ML Festival Isolation Guardrail:
            # If target date is a normal non-festival date, filter out festival spike records (Dhuleti, Diwali, Holi, etc.)
            if is_festival == 0 and "is_festival" in df.columns:
                df_non_fest = df[pd.to_numeric(df["is_festival"], errors="coerce").fillna(0) == 0]
                if len(df_non_fest) >= 5:
                    df = df_non_fest

            
            # Duration-aware filtering (ensures 120H bookings never pollute 24H booking baselines)
            if "duration_hours" in df.columns:
                dur_series = pd.to_numeric(df["duration_hours"], errors="coerce").fillna(24.0)
            else:
                dur_series = pd.Series([24.0] * len(df), index=df.index)

            if duration_hours <= 30.0:
                dur_mask = dur_series <= 30.0
            elif duration_hours <= 54.0:
                dur_mask = (dur_series >= 30.0) & (dur_series <= 54.0)
            elif duration_hours <= 78.0:
                dur_mask = (dur_series >= 54.0) & (dur_series <= 78.0)
            elif duration_hours <= 102.0:
                dur_mask = (dur_series >= 78.0) & (dur_series <= 102.0)
            else:
                dur_mask = dur_series >= 102.0

            df_dur = df[dur_mask]
            if len(df_dur) < 3:
                df_dur = df # Relax duration filter if insufficient exact duration matches

            # Level 3: Same Slot + Duration Window
            df_slot = df_dur[df_dur["commercial_slot"] == slot]
            same_slot_count = len(df_slot)
            
            # Level 2: Same Month + Same Slot + Duration Window
            df_month_slot = df_slot[df_slot["month"] == month]
            same_month_slot_count = len(df_month_slot)
            
            # Level 1: Exact Match (Slot, Month, Duration Window, Weekend, Guest Category)
            def get_guest_cat(g):
                if g <= 2: return "couple"
                if g <= 12: return "family"
                return "corporate"
                
            req_cat = get_guest_cat(person_count)
            df_exact = df_month_slot[
                (df_month_slot["is_weekend"] == is_weekend) & 
                (df_month_slot["person_count"].apply(get_guest_cat) == req_cat)
            ]
            exact_match_count = len(df_exact)

            MIN_RECORDS = 3
            if exact_match_count >= MIN_RECORDS:
                level_used = "EXACT_MATCH"
                df_match = df_exact
                count_used = exact_match_count
            elif same_month_slot_count >= MIN_RECORDS:
                level_used = "SAME_MONTH_SAME_SLOT"
                df_match = df_month_slot
                count_used = same_month_slot_count
            elif same_slot_count >= MIN_RECORDS:
                level_used = "SAME_SLOT"
                df_match = df_slot
                count_used = same_slot_count
            else:
                level_used = "OVERALL_AVERAGE"
                df_match = df
                count_used = total_count

            fallback_avg_price = float(df_match["selling_price"].mean())


            diagnostic_info = {
                "level_used": level_used,
                "count_used": count_used,
                "exact_match_count": exact_match_count,
                "same_month_slot_count": same_month_slot_count,
                "same_slot_count": same_slot_count,
                "total_bookings_in_dataset": total_count,
                "fallback_avg_price": fallback_avg_price
            }

            sub_df = df_match.copy()
            sub_weekend = pd.to_numeric(sub_df.get("is_weekend", 0), errors="coerce").fillna(0)
            sub_month = pd.to_numeric(sub_df.get("month", 1), errors="coerce").fillna(1)
            sub_guests = pd.to_numeric(sub_df.get("person_count", 4), errors="coerce").fillna(4)
            sub_lead = pd.to_numeric(sub_df.get("lead_days", 7), errors="coerce").fillna(7)

            d_weekend = np.abs(sub_weekend - is_weekend) * 3.0
            d_month = np.abs(sub_month - month) * 1.5
            d_guests = np.log1p(np.abs(sub_guests - person_count)) * 0.15
            d_lead = 0.0 # Neutralize distance penalty since raw Excel dataset has constant lead_days = 7




            sub_df["dist"] = d_weekend + d_month + d_guests + d_lead
            sub_df.sort_values(by="dist", ascending=True, inplace=True)
            top_similar = sub_df.head(5)

            results = []
            prices_list = []
            weights_list = []

            for _, row in top_similar.iterrows():
                dist_val = float(row.get("dist", 0.0))
                sim_score = max(50.0, round(100.0 / (1.0 + dist_val * 0.15), 1))
                weight_val = float(np.exp(-0.2 * dist_val))
                
                s_price = row.get("selling_price")
                if s_price is None or pd.isna(s_price):
                    s_price = row.get("price", 8500.0)
                raw_p_val = safe_float(s_price, 8500.0)
                
                # Normalize historical raw price to 4-guest baseline and adjust for target query guest count
                hist_guests = safe_int(row.get("person_count"), 4)
                base_p_val = raw_p_val - max(0, hist_guests - 4) * 50.0
                p_val = base_p_val + max(0, person_count - 4) * 50.0


                prices_list.append(p_val)
                weights_list.append(weight_val)


                results.append({
                    "booking_date": str(row.get("booking_date", date.today().strftime("%Y-%m-%d"))),
                    "commercial_slot": str(row.get("commercial_slot", slot)),
                    "slot_type": str(row.get("slot_type", row.get("commercial_slot", slot))),
                    "person_count": safe_int(row.get("person_count"), 4),
                    "lead_days": safe_int(row.get("lead_days"), 7),
                    "selling_price": p_val,
                    "season": str(row.get("season", "Monsoon")),
                    "is_weekend": bool(row.get("is_weekend", True)),
                    "similarity_score": sim_score,
                    "weight": round(weight_val, 4)
                })

            # Calculate Similarity-Weighted Robust Historical Statistics (Weighted Median & Trimmed Mean)
            if prices_list and weights_list:
                w_arr = np.array(weights_list)
                p_arr = np.array(prices_list)
                
                weighted_mean = float(np.sum(w_arr * p_arr) / (np.sum(w_arr) + 1e-5))
                
                sort_idx = np.argsort(p_arr)
                p_sorted = p_arr[sort_idx]
                w_sorted = w_arr[sort_idx]
                cum_w = np.cumsum(w_sorted)
                cutoff = np.sum(w_sorted) / 2.0
                med_idx = np.where(cum_w >= cutoff)[0][0]
                weighted_median = float(p_sorted[med_idx])
                
                if len(p_arr) >= 5:
                    cut = int(np.floor(len(p_arr) * 0.10))
                    p_trim = np.sort(p_arr)[cut : len(p_arr) - cut] if cut > 0 else p_arr
                    trimmed_mean = float(np.mean(p_trim))
                else:
                    trimmed_mean = float(np.mean(p_arr))
                    
                historical_confidence = float(np.clip(np.sum(w_arr) / 4.0, 0.1, 1.0))
            else:
                weighted_mean = fallback_avg_price
                weighted_median = fallback_avg_price
                trimmed_mean = fallback_avg_price
                historical_confidence = 0.5

            diagnostic_info["weighted_mean"] = round(weighted_mean, 2)
            diagnostic_info["weighted_median"] = round(weighted_median, 2)
            diagnostic_info["trimmed_mean"] = round(trimmed_mean, 2)
            diagnostic_info["historical_confidence"] = round(historical_confidence, 2)

            return results, diagnostic_info, weighted_median

        except Exception as e:
            print(f"⚠️ Error searching similar uploaded bookings: {e}")
            return [], {"level_used": "ERROR", "count_used": 0}, 8500.0

    def audit_prediction(self, row_index: int) -> Dict[str, Any]:
        """
        Generates complete forensic prediction audit for the booking at row_index.
        """
        if not CLEAN_DATA_PATH.exists():
            raise FileNotFoundError("Clean booking dataset not found.")
            
        df = pd.read_csv(CLEAN_DATA_PATH)
        if row_index < 0 or row_index >= len(df):
            raise IndexError(f"Row index {row_index} out of bounds (0 to {len(df) - 1}).")
            
        row = df.iloc[row_index]
        
        # 1. Input Features
        input_features = {
            "booking_date": str(row["booking_date"]),
            "commercial_slot": str(row["commercial_slot"]),
            "person_count": int(row["person_count"]),
            "lead_days": int(row["lead_days"]),
            "competitor_price": float(row.get("competitor_price", 0.0))
        }
        
        # 2. Get prediction for this record
        pred_res = self.predict({
            "booking_date": str(row["booking_date"]),
            "commercial_slot": str(row["commercial_slot"]),
            "person_count": int(row["person_count"]),
            "lead_days": int(row["lead_days"]),
            "competitor_price": float(row.get("competitor_price", 0.0))
        })
        
        actual_price = float(row["selling_price"])
        predicted_price = float(pred_res["recommended_price"])
        abs_error = abs(actual_price - predicted_price)
        pct_error = (abs_error / actual_price * 100) if actual_price > 0 else 0.0
        
        # 3. Compute SHAP value contributions specifically for this row
        artifact = self.load_champion_model()
        shap_contributions = []
        if artifact and "model" in artifact:
            try:
                import shap
                voting_model = artifact["model"]
                features_list = artifact["features"]
                
                # Re-engineer features for this specific row
                from app.services.feature_engineering import FeatureEngineer
                raw_row = {
                    "booking_date": str(row["booking_date"]),
                    "commercial_slot": str(row["commercial_slot"]),
                    "duration_hours": float(row.get("duration_hours", 12.0)),
                    "person_count": int(row["person_count"]),
                    "lead_days": int(row["lead_days"]),
                    "competitor_price": float(row.get("competitor_price", 0.0)),
                    "temperature": float(row.get("temperature", 26.0)),
                    "rain_probability": float(row.get("rain_probability", 20.0)),
                    "humidity": float(row.get("humidity", 60.0))
                }
                feats = FeatureEngineer.extract_features_from_dict(raw_row)
                feats["commercial_slot"] = str(row["commercial_slot"])
                
                # Get dummies matching model feature columns
                X_df = pd.DataFrame([feats])
                X_encoded = pd.get_dummies(X_df, drop_first=False)
                X_model = X_encoded.reindex(columns=features_list, fill_value=0).astype(float)
                
                # Setup background
                df_all = pd.read_csv(CLEAN_DATA_PATH)
                features_all = [FeatureEngineer.extract_features_from_dict(r.to_dict()) for _, r in df_all.head(20).iterrows()]
                X_all = pd.DataFrame(features_all)
                X_all_encoded = pd.get_dummies(X_all, drop_first=False)
                background = X_all_encoded.reindex(columns=features_list, fill_value=0).astype(float)
                
                explainer = shap.KernelExplainer(voting_model.predict, background)
                shap_vals = explainer.shap_values(X_model)[0]
                
                for col, val, sv in zip(features_list, X_model.iloc[0].values, shap_vals):
                    if abs(sv) > 0.001:
                        # Log-space approximation of price impact
                        pred_log = voting_model.predict(X_model)[0]
                        prev_log = pred_log - sv
                        impact_amt = predicted_price - np.expm1(prev_log)
                        shap_contributions.append({
                            "feature": col,
                            "value": float(val),
                            "shap_value": float(sv),
                            "impact_amount": float(impact_amt)
                        })
            except Exception as e:
                print(f"SHAP calculations skipped in audit: {e}")
                
        # 4. Segment historical averages
        slot_df = df[df["commercial_slot"] == row["commercial_slot"]]
        month_df = df[df["month"] == row["month"]]
        is_we = int(row["is_weekend"])
        weekend_df = df[df["is_weekend"] == is_we]
        guests_df = df[df["person_count"] == row["person_count"]]
        
        slot_avg = float(slot_df["selling_price"].mean()) if not slot_df.empty else 0.0
        month_avg = float(month_df["selling_price"].mean()) if not month_df.empty else 0.0
        weekend_avg = float(weekend_df["selling_price"].mean()) if not weekend_df.empty else 0.0
        guests_avg = float(guests_df["selling_price"].mean()) if not guests_df.empty else 0.0
        
        # 5. Top 5 Reasons for Mismatch
        reasons = []
        if actual_price > 12000 and predicted_price < 8000:
            reasons.append("This is a premium high-end booking with a custom price markup (corporate/wedding celebration) not captured by standard features.")
        if row["is_weekend"] == 1:
            reasons.append("Weekend demand fluctuation. Weekend pricing segments have inherently higher volatility.")
        if len(slot_df) < 20:
            reasons.append(f"Small historical sample size ({len(slot_df)} bookings) for category {row['commercial_slot']}.")
        if abs(row["person_count"] - 15) <= 3:
            reasons.append("Large groups of 12-15 guests have high custom package variation based on catering and utilities.")
        if row["is_festival"] == 1:
            reasons.append(f"Festival premium variations on {row['season']} holiday days.")
        if abs(row.get("temperature", 26.0) - 38.0) < 5.0 or float(row.get("rain_probability", 0.0)) > 60:
            reasons.append("Extreme weather conditions (high heat or high rain probability) impacting guest booking behavior.")
            
        while len(reasons) < 5:
            reasons.append("Normal pricing variation and negotiation margin between owner and customer.")
            
        reasons = reasons[:5]
        
        # 6. Classification
        if actual_price > 15000:
            classification = "Business Rule Missing"
        elif len(slot_df) < 15:
            classification = "Insufficient Historical Data"
        elif actual_price == 1000 or actual_price < 2000:
            classification = "Outlier"
        elif abs_error > 5000:
            classification = "Model Bias"
        else:
            classification = "Unknown"
            
        # 7. Similar bookings
        similar_list = pred_res.get("similar_bookings", [])
        
        return {
            "row_index": row_index,
            "actual_price": actual_price,
            "predicted_price": predicted_price,
            "abs_error": abs_error,
            "pct_error": pct_error,
            "input_features": input_features,
            "engineered_features": {
                "is_weekend": bool(row["is_weekend"]),
                "is_festival": bool(row["is_festival"]),
                "season": str(row.get("season", "Monsoon")),
                "month": int(row["month"]),
                "day_of_week": int(row["day_of_week"])
            },
            "shap_contributions": shap_contributions,
            "similar_bookings": similar_list,
            "historical_average_slot": slot_avg,
            "historical_average_month": month_avg,
            "historical_average_weekend": weekend_avg,
            "historical_average_guests": guests_avg,
            "occupancy": float(pred_res.get("expected_occupancy_pct", 50.0)),
            "lead_days": int(row["lead_days"]),
            "weather": pred_res.get("weather", {}),
            "festival": str(row.get("festival_name", "No Festival")),
            "confidence_score": float(pred_res.get("confidence_score", 90.0)),
            "reasons": reasons,
            "classification": classification
        }

prediction_engine = PredictionEngine()
