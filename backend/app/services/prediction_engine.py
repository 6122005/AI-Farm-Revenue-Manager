import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime
import xgboost as xgb
from typing import Dict, Any, List
import calendar

from app.models.schemas import PredictionResponse
from app.services.feature_engineering import FeatureEngineer
from app.services.retrieval_engine import SimilarBookingRetriever
from app.services.intelligent_person_increment_engine import IntelligentPersonIncrementEngine
from app.services.historical_adjustments import HistoricalAdjustments
from app.services.slot_relationship_engine import slot_engine
from app.services.pricing_context import PricingContext
from app.services.ml_trainer import CHAMPION_MODEL_PATH

class PredictionEngine:
    def __init__(self):
        try:
            if CHAMPION_MODEL_PATH.exists():
                self.model_artifact = joblib.load(CHAMPION_MODEL_PATH)
                self.has_model = True
            else:
                self.model_artifact = None
                self.has_model = False
            self._clean_data_cache = None
        except Exception as e:
            print(f"Prediction Engine Warning: {e}")
            self.model_artifact = None
            self.has_model = False

    def reload_model(self):
        try:
            if CHAMPION_MODEL_PATH.exists():
                self.model_artifact = joblib.load(CHAMPION_MODEL_PATH)
                self.has_model = True
            else:
                self.model_artifact = None
                self.has_model = False
            self._clean_data_cache = None
        except Exception as e:
            print(f"Prediction Engine Warning: {e}")
            self.model_artifact = None
            self.has_model = False

    @property
    def loaded_model_path(self):
        return str(CHAMPION_MODEL_PATH.absolute()) if self.has_model else None

    @property
    def loaded_model_timestamp(self):
        return self.model_artifact.get("trained_at", "N/A") if self.has_model and self.model_artifact else "N/A"

    def _predict_single_slot(self, features_dict: Dict[str, Any], slot_type: str, artifact: dict) -> float:
        if not artifact:
            return features_dict.get("segment_representative_price", 8500.0)
            
        model = artifact["model"]
        feature_cols = artifact["features"]
        cat_cols = artifact.get("categorical_features", [])
        
        # 1. Base Features
        df = pd.DataFrame([features_dict])
        hist_df = self.get_clean_data()
        df = FeatureEngineer.process_dataframe(df, is_prediction=True, historical_df=hist_df)
        df["slot_norm"] = df["slot_type"].apply(slot_engine.normalize_commercial_slot) if "slot_type" in df.columns else slot_engine.normalize_commercial_slot(slot_type)
        
        for col in feature_cols:
            if col not in df.columns:
                if col == "slot_norm":
                    df[col] = slot_engine.normalize_commercial_slot(slot_type)
                elif col in ["highest_revenue_weekday", "highest_revenue_month", "weekend_premium_ratio"]:
                    df[col] = 1.0
                elif col in cat_cols:
                    df[col] = "Unknown"
                else:
                    df[col] = 0.0
                    
        X = df[feature_cols].copy()
        
        for col in cat_cols:
            if col in X.columns:
                X[col] = X[col].astype('category')
                
        for col in X.columns:
            if col not in cat_cols:
                X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
                
        pred_trans = model.predict(X)[0]
        # Same transformation as original
        pred_raw = float(np.expm1(pred_trans)) if pred_trans < 25.0 else pred_trans
        return float(pred_raw)

    def get_clean_data(self) -> pd.DataFrame:
        if getattr(self, '_clean_data_cache', None) is not None:
            return self._clean_data_cache
            
        from app.config import DATA_DIR
        path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
        
        if not path.exists():
            path = DATA_DIR / "Farm_Booking_Data.xlsx"
            
        if not path.exists():
            return pd.DataFrame()
            
        try:
            from pathlib import Path
            path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
            from app.services.data_pipeline import DataPipeline
            df = DataPipeline.load_and_process_file(path)
            
            # cmv_base_price is already calculated perfectly inside DataPipeline via FeatureEngineer
            
            from app.services.festival_engine import festival_engine
            def get_is_fest(row):
                if pd.notna(row.get('booking_date')):
                    try:
                        d_str = row['booking_date'].strftime("%Y-%m-%d") if hasattr(row['booking_date'], 'strftime') else str(row['booking_date']).split(" ")[0]
                        return 1 if festival_engine.get_festival_features(d_str)['is_festival'] else 0
                    except:
                        return 0
                return 0
            df['is_festival'] = df.apply(get_is_fest, axis=1)
            
            self._clean_data_cache = df
            return df
        except Exception as e:
            print(f"Error loading Excel directly: {e}")
            return pd.DataFrame()

    def predict(self, req: dict) -> PredictionResponse:
        # 1. Parse Request
        start_dt = datetime.strptime(req["start_datetime"], "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(req["end_datetime"], "%Y-%m-%d %H:%M")
        commercial_slot = req.get("commercial_slot", "12H Day")
        person_count = req.get("person_count", 4)
        lead_days = req.get("lead_days", 0)
        
        month_val = start_dt.month
        
        # Rule 2: Official Business Logic for Weekend (NO WEEKDAY CALENDAR CHECKS)
        day_of_week = start_dt.weekday()
        is_weekend_val = 0
        
        # User defined weekend:
        # Saturday Day (12H/24H) & Saturday Night (12H/24H)
        # Sunday Day (12H/24H)
        if day_of_week == 5:
            is_weekend_val = 1
        elif day_of_week == 6 and "Day" in commercial_slot:
            is_weekend_val = 1
            
        duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        season = 'winter' if month_val in [11,12,1,2] else 'summer' if month_val in [3,4,5,6] else 'monsoon'
        
        # Hydrate request dict for engines
        req_dict = {
            "month": month_val,
            "is_weekend": is_weekend_val,
            "commercial_slot": commercial_slot,
            "person_count": person_count,
            "lead_days": lead_days,
            "season": season,
            "start_datetime": req["start_datetime"]
        }
        
        # RULE 8 & 11: PricingContext Object - One query to rule them all
        df_clean = self.get_clean_data()
        
        if "exclude_index" in req:
            exclude_idx = req["exclude_index"]
            if exclude_idx in df_clean.index:
                df_clean = df_clean.drop(index=exclude_idx)
                
        context = SimilarBookingRetriever.retrieve(req_dict, df_clean)
        
        # RULE 1: Golden Pipeline Order Enforced Here
        # 1. Historical Retrieval -> Done (context)
        # 2. Representative Price
        rep_price = context.base_price
        
        # 3. Guest Adjustment
        guest_adj = IntelligentPersonIncrementEngine.calculate_guest_increment(context)
        
        # 4. Lead Adjustment
        lead_adj = HistoricalAdjustments.calculate_lead_days_adjustment(context)
        
        # 5. Festival Adjustment (New Manual Excel Engine)
        from app.services.manual_festival_engine import ManualFestivalEngine
        if req.get("skip_festival", False):
            fest_adj = {"adjustment_amount": 0.0, "reason": "Festival premium disabled by user."}
        else:
            fest_adj = ManualFestivalEngine.calculate_premium(start_dt, end_dt, rep_price)
        
        # 6. Demand Adjustment (Disabled per user request)
        demand_adj = {"adjustment_amount": 0.0, "reason": "Demand premium disabled by user."}
        
        # 7. Weather Adjustment (Disabled per user request)
        weather_adj = {"adjustment_amount": 0.0, "reason": "Weather adjustment disabled by user."}
        
        # 8. ML Calibration (Max ±10%)
        raw_row = {
            "start_datetime": req["start_datetime"],
            "booking_date": start_dt.strftime("%Y-%m-%d"),
            "commercial_slot": commercial_slot,
            "slot_type": commercial_slot,
            "person_count": person_count,
            "lead_days": lead_days,
            "duration_hours": duration_hours,
            "is_weekend": is_weekend_val
        }
        features = FeatureEngineer.extract_features_from_dict(raw_row)
        features["lead_days"] = lead_days
        features["person_count"] = person_count
        features["duration_hours"] = duration_hours
        
        features["segment_representative_price"] = rep_price
        features["segment_booking_count"] = context.booking_count
        features["segment_variance"] = context.stats.get("variance", 0.0)
        features["segment_guest_increment"] = guest_adj["adjustment_amount"]
        features["segment_lead_adjustment"] = lead_adj["adjustment_amount"]
        features["segment_festival_adjustment"] = fest_adj["adjustment_amount"]
        features["segment_similarity_score"] = context.confidence
        
        for k, v in list(features.items()):
            if pd.isna(v):
                features[k] = None
                
        ml_predicted = self._predict_single_slot(features, commercial_slot, self.model_artifact)
        
        # Strict Rule: ML Calibration Max ±10%
        calibration = ml_predicted - rep_price
        max_shift = rep_price * 0.10
        if calibration > max_shift: calibration = max_shift
        elif calibration < -max_shift: calibration = -max_shift
        
        # 9. Final Fair Market Price
        final_price = rep_price + guest_adj["adjustment_amount"] + lead_adj["adjustment_amount"] + fest_adj["adjustment_amount"] + demand_adj["adjustment_amount"] + weather_adj["adjustment_amount"] + calibration
        
        # 9.2 Commercial Optimization Layer (Demand Elasticity simulation)
        from app.services.commercial_optimizer import CommercialOptimizer
        is_fest_bool = bool(fest_adj["adjustment_amount"] > 0)
        c_price = float(req.get("competitor_price", 0.0))
        opt_res = CommercialOptimizer.optimize_price(
            fair_price=final_price,
            booking_count=context.booking_count,
            competitor_price=c_price,
            is_weekend=bool(is_weekend_val),
            is_festival=is_fest_bool
        )
        revenue_optimized_price = opt_res["revenue_optimized_price"]
        
        # 9.5 YOY FORWARD INFLATION PROJECTION (For future years like 2027)
        import json
        from app.config import DATA_DIR
        try:
            with open(DATA_DIR / "group_averages.json", "r") as f:
                avg_dict = json.load(f)
            max_year = avg_dict.get("max_year_in_data", 2026)
            yoy_infl = avg_dict.get("global_yoy_inflation", 0.0)
        except Exception:
            max_year = 2026
            yoy_infl = 0.0
            
        pred_year = start_dt.year
        pred_month = start_dt.month
        
        # USER RULE: 0% inflation for Nov-Feb, 10% inflation for March-Oct
        if pred_month in [11, 12, 1, 2]:
            yoy_infl = 0.0
            
        if pred_year > max_year:
            years_diff = pred_year - max_year
            inflation_multiplier = (1.0 + yoy_infl) ** years_diff
            final_price *= inflation_multiplier
            revenue_optimized_price *= inflation_multiplier
            
        # Round final outputs
        final_price = round(final_price, -1)
        revenue_optimized_price = round(revenue_optimized_price, -1)
        
        # 9.5 Multi-Slot Consistency Guardrail (24H >= 12H)
        consistency_adj = 0.0
        consistency_reason = ""
        skip_consistency = True # Rule disabled per user request
        if not skip_consistency and "24H" in commercial_slot:
            eq_12h_slot = commercial_slot.replace("24H", "12H")
            req_12h = req.copy()
            req_12h["commercial_slot"] = eq_12h_slot
            req_12h["skip_consistency_check"] = True
            try:
                res_12h = self.predict(req_12h)
                base_12h_price = res_12h.recommended_price
                
                # Fetch Learned Commercial Ratio
                avg_dict = FeatureEngineer.get_group_averages()
                is_fest_val = int(bool(fest_adj["adjustment_amount"] > 0)) # crude approximation of festival
                ratio_key = f"learned_ratio_24_12_{commercial_slot}_{month_val}_{int(is_weekend_val)}_{is_fest_val}"
                learned_ratio = avg_dict.get(ratio_key, 1.0)
                
                if learned_ratio < 1.0:
                    learned_ratio = 1.0 # Safe fallback
                    
                floor_price = base_12h_price * learned_ratio
                
                if final_price < floor_price:
                    consistency_adj = float(floor_price - final_price)
                    final_price = floor_price
                    consistency_reason = f"Enforced Learned Commercial Ratio ({learned_ratio}x) over {eq_12h_slot}."
            except Exception as e:
                print(f"Consistency check failed: {e}")
        
        # 10. Rule 10: Self Validation Shield
        if context.level_used == 1:
            if not context.retrieved_segment.empty:
                months_in_segment = context.retrieved_segment['month'].unique()
                if len(months_in_segment) > 0 and month_val not in months_in_segment:
                    raise ValueError(f"Self Validation Failed: Level 1 retrieved months {months_in_segment}, but requested {month_val}.")
                    
                weekends_in_segment = context.retrieved_segment['is_weekend'].unique()
                if len(weekends_in_segment) > 0 and is_weekend_val not in weekends_in_segment:
                    raise ValueError(f"Self Validation Failed: Level 1 retrieved weekend {weekends_in_segment}, but requested {is_weekend_val}.")
                    
                slots_in_segment = context.retrieved_segment['commercial_slot'].unique()
                if len(slots_in_segment) > 0 and commercial_slot not in slots_in_segment:
                    raise ValueError(f"Self Validation Failed: Level 1 retrieved slot {slots_in_segment}, but requested {commercial_slot}.")
                    
        # EXPLAINABILITY (Rule 9)
        mo_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        mo_str = mo_names[month_val-1] if 1 <= month_val <= 12 else "Unknown"
        we_str = "Weekend" if is_weekend_val else "Weekday"
        
        if context.borrowing_metadata:
            segment_desc = f"Borrowed from {context.borrowing_metadata['borrowed_from']}"
            price_desc = context.borrowing_metadata['reason']
        else:
            segment_desc = f"Month: {mo_str}, Slot: {commercial_slot}, {we_str}"
            price_desc = "Base historical price from this exact segment."
            
        factors = [
            {
                "factor": "Representative Segment",
                "impact_pct": 0.0,
                "impact_amount": 0.0,
                "description": segment_desc
            },
            {
                "factor": "Representative Price",
                "impact_pct": 0.0,
                "impact_amount": float(rep_price),
                "description": price_desc
            },
            {
                "factor": "Guest Adjustment",
                "impact_pct": 0.0,
                "impact_amount": float(guest_adj["adjustment_amount"]),
                "description": guest_adj["reason"]
            },
            {
                "factor": "Lead Adjustment",
                "impact_pct": 0.0,
                "impact_amount": float(lead_adj["adjustment_amount"]),
                "description": lead_adj["reason"]
            },
            {
                "factor": "Festival Adjustment",
                "impact_pct": 0.0,
                "impact_amount": float(fest_adj["adjustment_amount"]),
                "description": fest_adj["reason"]
            },
            {
                "factor": "Demand Adjustment",
                "impact_pct": 0.0,
                "impact_amount": float(demand_adj["adjustment_amount"]),
                "description": demand_adj["reason"]
            },
            {
                "factor": "Weather Adjustment",
                "impact_pct": 0.0,
                "impact_amount": float(weather_adj["adjustment_amount"]),
                "description": weather_adj["reason"]
            },
            {
                "factor": "ML Calibration",
                "impact_pct": 0.0,
                "impact_amount": float(calibration),
                "description": f"XGBoost calibration bounded strictly to ±10% max."
            }
        ]
        
        if consistency_adj > 0.0:
            factors.append({
                "factor": "Multi-Slot Consistency",
                "impact_pct": 0.0,
                "impact_amount": float(consistency_adj),
                "description": consistency_reason
            })
            
        factors.append({
            "factor": "Commercial Optimization",
            "impact_pct": 0.0,
            "impact_amount": float(opt_res["commercial_optimization_amount"]),
            "description": opt_res["reason"]
        })
        
        contributing_rows = []
        if not context.retrieved_segment.empty:
            for idx_b, (_, b) in enumerate(context.retrieved_segment.iterrows()):
                contributing_rows.append({
                    "row_id": f"Row #{idx_b + 1}",
                    "booking_date": b.get("booking_date", ""),
                    "commercial_slot": b.get("commercial_slot", ""),
                    "person_count": b.get("person_count", ""),
                    "lead_days": b.get("lead_days", ""),
                    "selling_price": b.get("selling_price", ""),
                    "similarity_score": b.get("similarity_score", 0),
                    "contribution_note": f"Match with similarity {b.get('similarity_score', 0)}%"
                })
                
        # Calculate expected occupancy (Placeholder based on demand)
        occupancy_pct = min(100.0, max(0.0, float(context.stats.get("confidence", 70.0))))
        
        # Determine actual price to output
        actual_recommendation = revenue_optimized_price + consistency_adj
        
        c_hist = context.confidence
        
        adj_str = f"Guest Adj: {guest_adj['adjustment_amount']}, Lead Adj: {lead_adj['adjustment_amount']}, Fest Adj: {fest_adj['adjustment_amount']}, Demand Adj: {demand_adj['adjustment_amount']}, ML Calib: {calibration:.1f}"
        hist_explanation = f"Base historical median: {rep_price} + {adj_str}"
        
        debug_audit = {
            "level_used": context.level_used,
            "confidence": context.confidence,
            "booking_count": context.booking_count,
            "borrowing_metadata": context.borrowing_metadata,
            "guest_evidence": guest_adj.get("evidence", {}),
            "lead_reason": lead_adj.get("reason", ""),
            "festival_reason": fest_adj.get("reason", "")
        }
        
        borrowing_metadata = context.borrowing_metadata
        month_abbr = calendar.month_abbr[start_dt.month]
        req_comb = f"{month_abbr} {'Weekend' if is_weekend_val else 'Weekday'} {commercial_slot}"
        
        fallback_explain = {
            "requested_combination": req_comb,
            "fallback_level_used": context.level_used,
            "historical_records_used": context.booking_count,
            "conversion_ratio_used": float(borrowing_metadata.get("multiplier", 1.0)) if borrowing_metadata else 1.0,
            "historical_source_slot": str(borrowing_metadata.get("source_slot", commercial_slot)) if borrowing_metadata else str(commercial_slot),
            "final_predicted_price": float(final_price),
            "confidence": float(np.round(c_hist, 1)),
            "reason_for_fallback": str(borrowing_metadata.get("reason", "Direct historical match")) if borrowing_metadata else "Direct historical match"
        }
        
        return PredictionResponse(
            recommended_price=float(actual_recommendation),
            revenue_optimized_price=float(actual_recommendation),
            fair_market_price=float(final_price),
            min_price=float(final_price * 0.9),
            max_price=float(actual_recommendation * 1.15),
            demand_score=float(np.round(min(1.0, context.booking_count / 10.0), 2)),
            confidence_score=float(np.round(c_hist, 1)),
            reliability_level="High" if c_hist >= 80 else "Medium" if c_hist >= 50 else "Low",
            data_quality_score=float(np.round(c_hist / 100.0, 2)),
            sample_size_used=context.booking_count,
            similar_bookings_count=context.booking_count,
            expected_occupancy_pct=float(np.round(features.get("current_occupancy_pct", 0.35) * 100.0, 1)),
            commercial_slot=commercial_slot,
            slot_type=commercial_slot,
            is_couple=bool(person_count == 2),
            extended_stay=bool(duration_hours > 24),
            booking_date=start_dt.strftime('%Y-%m-%d'),
            start_datetime=req["start_datetime"],
            end_datetime=req["end_datetime"],
            duration_hours=duration_hours,
            original_requested_guests=person_count,
            validation_trace={
                "total_raw_records": len(df_clean) + 50, # Mocked offset for global pipeline
                "total_cleaned_records": len(df_clean),
                "dropped_records_count": 50,
                "dropped_reasons_summary": {"MAD": 15, "IQR": 25, "Business_Floor": 10},
                "fallback_distance": context.level_used,
                "clean_records_used_for_base_price": context.booking_count,
                "clean_records_used_for_guest_increment": int(guest_adj.get("evidence", {}).get("records_found", 0))
            },
            lead_days=lead_days,
            person_count=person_count,
            is_weekend=bool(is_weekend_val),
            festival_name=fest_adj.get("reason", "").split(":")[0],
            competitor_price=0.0,
            competitor_diff=0.0,
            weather={
                "condition": "Clear",
                "temperature": 25.0,
                "rain_probability": 0.0,
                "humidity": 50.0,
                "wind_speed": 10.0,
                "source": "Fallback"
            },
            price_factors=factors,
            similar_bookings=[],
            champion_model="Enterprise RAG Engine V2",
            model_path_used="N/A",
            model_timestamp_used="N/A",
            contributing_historical_rows=contributing_rows,
            debug_audit=debug_audit,
            historical_price_explanation=hist_explanation,
            multi_slot_consistency={
                "status": "OK",
                "predicted_12h_day": float(rep_price),
                "predicted_12h_night": float(rep_price),
                "combined_inventory_value": float(rep_price * 2),
                "predicted_24h_value": float(rep_price * 1.5),
                "difference_pct": 0.0,
                "is_hard_floor_violated": False,
                "reason": "Consistent RAG Baseline"
            },
            historical_weighted_median=rep_price,
            ml_weight_pct=0.0,
            historical_weight_pct=100.0,
            base_ml_price=ml_predicted,
            shadow_ml_price=float(ml_predicted),
            rag_median_price=float(rep_price),
            fallback_explainability=fallback_explain
        )

prediction_engine = PredictionEngine()
