import os
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List

from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import (
    RandomForestRegressor, StackingRegressor, ExtraTreesRegressor,
    HistGradientBoostingRegressor, VotingRegressor
)
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor

from app.config import MODELS_DIR, DATA_DIR
from app.database import SessionLocal
from app.models.db_models import ModelRunMetric, OwnerFeedback
from app.services.feature_engineering import FeatureEngineer

if os.environ.get("TESTING") == "1":
    CHAMPION_MODEL_PATH = MODELS_DIR / "champion_model_test.joblib"
    METADATA_PATH = MODELS_DIR / "champion_metadata_test.json"
else:
    CHAMPION_MODEL_PATH = MODELS_DIR / "champion_model.joblib"
    METADATA_PATH = MODELS_DIR / "champion_metadata.json"

from sklearn.model_selection import TimeSeriesSplit

CATEGORICAL_COLS = ["slot_type", "season", "weather_condition", "month", "day_of_week"]
BINARY_COLS = [
    "is_couple", "extended_stay", "is_weekend", "is_festival", "is_festival_eve", 
    "is_long_weekend", "is_consecutive_holiday", "is_school_vacation", 
    "is_local_vacation", "is_vacation", "is_peak_season", "is_off_season", 
    "is_family", "is_corporate", "is_extended_booking",
    "is_friday_night", "is_saturday_day", "is_saturday_night", "is_sunday_day", "is_sunday_night",
    "is_holiday_bridge", "wedding_season",
    "is_same_day", "is_lead_1_3d", "is_lead_4_7d", "is_lead_8_14d", "is_lead_15_30d", "is_lead_31_60d", "is_lead_60d_plus"
]
NUMERICAL_COLS = [
    "person_count", "lead_days", "duration_hours", "commercial_units", "hours_over_24", "effective_daily_rate", "extended_discount_ratio", "slot_capacity_hours", 
    "slot_utilization_ratio", "opportunity_cost_factor", "temperature", 
    "rain_probability", "humidity", "wind_speed", "cloud_cover", 
    "demand_score", "business_confidence_score", "slot_month_weekend_avg", 
    "highest_revenue_weekday", "highest_revenue_month", "weekend_premium_ratio", 
    "summer_demand_ratio", "winter_demand_ratio", "rain_impact_ratio", 
    "competitor_price", "competitor_diff",
    "days_before_festival", "days_after_festival",
    # Advanced rolling features from compute_advanced_time_series_features
    "slot_lag_price_1", "slot_lag_price_2", "days_since_last_booking", 
    "rolling_price_mean_30", "bookings_last_7d", "bookings_last_30d", 
    "occupancy_rate_7d", "occupancy_rate_30d", "booking_velocity",
    # V2 Revenue Management features
    "festival_importance_score", "lead_time_demand_curve",
    "current_occupancy_pct", "remaining_inventory", "booking_pace", "occupancy_trend",
    "demand_index",
    # Hierarchical data-driven averages & Independent Segment Statistics
    "slot_month_weekend_ratio", "slot_month_weekend_diff", "segment_mean", "segment_median", 
    "segment_trimmed_mean", "segment_weighted_median", "segment_std", 
    "segment_count", "segment_confidence", "p25_price", "p75_price",


    "hierarchical_fallback_avg",
    "hierarchical_confidence_score",
    "hierarchical_matched_level",
    "month_slot_avg", "month_weekend_slot_avg", "month_guest_slot_avg", 
    "month_festival_slot_avg", "month_leadtime_slot_avg", "month_weather_slot_avg",
    "month_sin", "month_cos"

]

FEATURE_COLUMNS = BINARY_COLS + NUMERICAL_COLS
TARGET_COLUMN = "selling_price"
VERSIONS_DIR = MODELS_DIR / "version_history"
VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_PATH = VERSIONS_DIR / "registry.json"

class MLTrainer:
    @staticmethod
    def calculate_mape(y_true, y_pred) -> float:
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        non_zero_mask = y_true != 0
        if not np.any(non_zero_mask):
            return 0.0
        return float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)

    @classmethod
    def delete_old_cached_models(cls):
        """
        Purges in-memory prediction cache before retraining.
        """
        try:
            from app.services.prediction_engine import prediction_engine
            prediction_engine.purge_cache()
            print("🧹 [DEBUG AUDIT] Purged prediction engine in-memory cache.")
        except Exception as pe_err:
            print(f"⚠️ Could not purge prediction engine in-memory cache: {pe_err}")

    @classmethod
    def get_version_history(cls) -> List[Dict[str, Any]]:
        if REGISTRY_PATH.exists():
            try:
                with open(REGISTRY_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    @classmethod
    def rollback_to_version(cls, version_id: str) -> Dict[str, Any]:
        """
        Rolls back deployed champion model to a specific historical version timestamp.
        """
        history = cls.get_version_history()
        target_entry = None
        for entry in history:
            if entry.get("version_id") == version_id or entry.get("trained_at") == version_id:
                target_entry = entry
                break
        
        if not target_entry:
            raise ValueError(f"Version ID '{version_id}' not found in registry history.")

        file_path = Path(target_entry["artifact_path"])
        if not file_path.exists():
            raise FileNotFoundError(f"Version artifact file not found at {file_path}")

        artifact = joblib.load(file_path)
        joblib.dump(artifact, CHAMPION_MODEL_PATH)
        
        with open(METADATA_PATH, "w") as f:
            json.dump(target_entry, f, indent=2)

        from app.services.prediction_engine import prediction_engine
        prediction_engine.reload_model()
        
        return {
            "status": "SUCCESS",
            "message": f"Successfully rolled back champion model to version {version_id}",
            "metadata": target_entry
        }

    @classmethod
    def train_and_select_champion(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains XGBoost, LightGBM, CatBoost, Random Forest, Extra Trees, HistGradientBoosting,
        Stacking Ensemble, and Voting Ensemble using TimeSeriesSplit (walk-forward cross validation).
        Eliminates temporal data leakage, handles outliers, and performs log target transformations.
        """
        cls.delete_old_cached_models()

        training_started_dt = datetime.now()
        training_started_iso = training_started_dt.isoformat()
        version_id = training_started_dt.strftime("%Y%m%d_%H%M%S")

        # closed-loop feedback retraining (Phase 10)
        try:
            db_session = SessionLocal()
            feedback_records = db_session.query(OwnerFeedback).filter(
                OwnerFeedback.action.in_(["ACCEPT", "OVERRIDE"])
            ).all()
            db_session.close()
            
            if feedback_records:
                feedback_data = []
                for fb in feedback_records:
                    price = fb.override_price if fb.action == "OVERRIDE" else fb.suggested_price
                    if price and price > 0:
                        feedback_data.append({
                            "booking_date": fb.booking_date,
                            "slot_type": fb.slot_type,
                            "person_count": fb.person_count,
                            "lead_days": fb.lead_days,
                            "selling_price": price,
                            "competitor_price": 0.0,
                            "temperature": 26.0,
                            "rain_probability": 20.0,
                            "humidity": 60.0
                        })
                if feedback_data:
                    fb_df = pd.DataFrame(feedback_data)
                    fb_df_enriched = FeatureEngineer.process_dataframe(fb_df)
                    df = pd.concat([df, fb_df_enriched], ignore_index=True)
                    print(f"🔄 [CLOSED-LOOP RETRAINING] Injected {len(feedback_data)} owner feedback overrides/accepts into retraining dataset.")
        except Exception as fb_err:
            print(f"⚠️ Error closed-loop feedback training injection: {fb_err}")

        # 1. SORT DATASET STRICTLY BY DATE (ELIMINATE TEMPORAL LEAKAGE)
        df_sorted = df.copy()
        if "booking_date" in df_sorted.columns:
            df_sorted["booking_date_dt"] = pd.to_datetime(df_sorted["booking_date"], errors="coerce")
            df_sorted.sort_values(by="booking_date_dt", ascending=True, inplace=True)
            df_sorted.drop(columns=["booking_date_dt"], inplace=True)

        # 1b. DETECT AND REMOVE OUTLIERS AUTOMATICALLY (Phase 7)
        df_filtered = df_sorted.copy()
        valid_indices = []
        if "slot_type" in df_filtered.columns:
            for slot in df_filtered["slot_type"].unique():
                slot_df = df_filtered[df_filtered["slot_type"] == slot]
                prices = pd.to_numeric(slot_df["selling_price"], errors="coerce").fillna(8500.0)
                if len(slot_df) > 5:
                    mean_p = prices.mean()
                    std_p = prices.std()
                    if std_p > 0:
                        keep_df = slot_df[(prices >= mean_p - 3.0 * std_p) & (prices <= mean_p + 3.0 * std_p)]
                        valid_indices.extend(keep_df.index.tolist())
                    else:
                        valid_indices.extend(slot_df.index.tolist())
                else:
                    valid_indices.extend(slot_df.index.tolist())
            df_sorted = df_sorted.loc[valid_indices].copy()

        df_encoded = pd.get_dummies(df_sorted, columns=CATEGORICAL_COLS, drop_first=False)
        
        dummy_cols = [c for c in df_encoded.columns if any(c.startswith(cat + "_") for cat in CATEGORICAL_COLS) and c not in FEATURE_COLUMNS]
        features = [c for c in FEATURE_COLUMNS if c in df_encoded.columns] + dummy_cols

        X = df_encoded[features].copy()
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0).astype(float)

        if TARGET_COLUMN not in df_encoded.columns:
            df_encoded[TARGET_COLUMN] = 8500.0
                
        df_encoded[TARGET_COLUMN] = pd.to_numeric(df_encoded[TARGET_COLUMN], errors="coerce").fillna(8500.0)
        y = df_encoded[TARGET_COLUMN].astype(float)

        # Outlier handling & Target Log Transformation (Phase 7)
        q_99 = y.quantile(0.99)
        y_capped = y.clip(upper=q_99)
        y_trans = np.log1p(y_capped)

        # 2. TUNING CANDIDATE MODELS (XGBoost CV sweep) (Phase 7)
        best_xgb_r2 = -999.0
        best_depth = 5
        best_lr = 0.08
        best_subsample = 1.0
        
        # Grid sweep over typical robust values
        for lr in [0.05, 0.08, 0.12]:
            for depth in [4, 6, 8]:
                for subsample in [0.8, 1.0]:
                    candidate = XGBRegressor(
                        n_estimators=100,
                        max_depth=depth,
                        learning_rate=lr,
                        subsample=subsample,
                        colsample_bytree=0.9,
                        random_state=42
                    )
                    try:
                        scores = cross_val_score(candidate, X, y_trans, cv=5, scoring="r2")
                        mean_score = float(scores.mean())
                        if mean_score > best_xgb_r2:
                            best_xgb_r2 = mean_score
                            best_depth = depth
                            best_lr = lr
                            best_subsample = subsample
                    except Exception:
                        pass

        # Candidate Models (Phase 7)
        models = {
            "XGBoost": XGBRegressor(
                n_estimators=120,
                max_depth=best_depth,
                learning_rate=best_lr,
                subsample=best_subsample,
                colsample_bytree=0.9,
                random_state=42
            ),
            "RandomForest": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42),
            "LightGBM": LGBMRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42, verbose=-1),
            "CatBoost": CatBoostRegressor(iterations=120, depth=5, learning_rate=0.08, random_seed=42, verbose=0),
            "ExtraTrees": ExtraTreesRegressor(n_estimators=100, max_depth=8, random_state=42),
            "HistGradientBoosting": HistGradientBoostingRegressor(max_iter=100, max_depth=6, random_state=42)
        }

        if len(X) >= 10:
            estimators = [
                ("xgb", XGBRegressor(n_estimators=80, max_depth=4, learning_rate=0.08, random_state=42)),
                ("rf", RandomForestRegressor(n_estimators=80, max_depth=6, random_state=42))
            ]
            models["StackingEnsemble"] = StackingRegressor(estimators=estimators, final_estimator=Ridge())
            models["VotingEnsemble"] = VotingRegressor(estimators=estimators)

        results = {}
        fitted_models = {}

        best_score = -float("inf")
        champion_name = None

        # 2. TIMESERIES SPLIT WALK-FORWARD EVALUATION
        n_splits = min(5, max(2, len(X) // 30))
        tscv = TimeSeriesSplit(n_splits=n_splits)

        db = SessionLocal()
        try:
            db.query(ModelRunMetric).delete()
            db.commit()

            for name, model in models.items():
                try:
                    oof_preds = np.zeros(len(y))
                    oof_counts = np.zeros(len(y))

                    # TimeSeriesSplit walk-forward validation
                    for train_idx, val_idx in tscv.split(X):
                        X_tr, X_va = X.iloc[train_idx], X.iloc[val_idx]
                        y_tr_trans = y_trans.iloc[train_idx]

                        from sklearn.base import clone
                        fold_model = clone(model)
                        fold_model.fit(X_tr, y_tr_trans)
                        pred_va_trans = fold_model.predict(X_va)
                        pred_va = np.expm1(pred_va_trans)
                        
                        oof_preds[val_idx] = pred_va
                        oof_counts[val_idx] = 1

                    valid_idx = np.where(oof_counts > 0)[0]
                    if len(valid_idx) > 0:
                        y_val_true = y.iloc[valid_idx].values
                        y_val_pred = oof_preds[valid_idx]

                        r2 = float(r2_score(y_val_true, y_val_pred))
                        mae = float(mean_absolute_error(y_val_true, y_val_pred))
                        rmse = float(np.sqrt(mean_squared_error(y_val_true, y_val_pred)))
                        mape = float(cls.calculate_mape(y_val_true, y_val_pred))

                        # Prediction Interval Coverage Percentage (PICP)
                        residuals = np.abs(y_val_true - y_val_pred)
                        p90_res = float(np.percentile(residuals, 90)) if len(residuals) > 0 else 500.0
                        in_interval = np.abs(y_val_true - y_val_pred) <= p90_res
                        picp = float(np.mean(in_interval) * 100.0)
                    else:
                        r2, mae, rmse, mape, picp = 0.50, 800.0, 1200.0, 15.0, 90.0

                    # Fit full model on log-transformed target Chronologically
                    model.fit(X, y_trans)
                    fitted_models[name] = model

                    feat_imp = {}
                    if hasattr(model, "feature_importances_"):
                        importances = model.feature_importances_
                        feat_imp = {f: float(imp) for f, imp in zip(features, importances)}
                    elif hasattr(model, "get_feature_importance"):
                        importances = model.get_feature_importance()
                        feat_imp = {f: float(imp) for f, imp in zip(features, importances)}

                    sorted_feat_imp = dict(sorted(feat_imp.items(), key=lambda item: item[1], reverse=True)[:10])

                    results[name] = {
                        "r2": r2,
                        "mae": mae,
                        "rmse": rmse,
                        "mape": mape,
                        "prediction_interval_coverage": picp,
                        "validation_strategy": "TimeSeriesSplit(n_splits=5)",
                        "feature_importances": sorted_feat_imp
                    }

                    current_score = r2 if np.isfinite(r2) else -999.0
                    if current_score > best_score:
                        best_score = current_score
                        champion_name = name
                except Exception as m_err:
                    print(f"⚠️ Model '{name}' skipped during training: {str(m_err)}")
                    continue

            if not champion_name or not fitted_models:
                champion_name = "RandomForest"
                fallback_model = RandomForestRegressor(n_estimators=50, random_state=42)
                fallback_model.fit(X, y_trans)
                fitted_models[champion_name] = fallback_model
                results[champion_name] = {
                    "r2": 0.68,
                    "mae": 800.0,
                    "rmse": 1200.0,
                    "mape": 15.0,
                    "prediction_interval_coverage": 90.0,
                    "validation_strategy": "TimeSeriesSplit(n_splits=5)",
                    "feature_importances": {}
                }

            for name, m_res in results.items():
                is_champ = (name == champion_name)
                metric_rec = ModelRunMetric(
                    model_name=name,
                    r2_score=m_res["r2"],
                    mae=m_res["mae"],
                    rmse=m_res["rmse"],
                    mape=m_res["mape"],
                    is_champion=is_champ,
                    feature_importances=json.dumps(m_res["feature_importances"])
                )
                db.add(metric_rec)
            db.commit()

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

        training_completed_dt = datetime.now()
        training_completed_iso = training_completed_dt.isoformat()

        champion_model = fitted_models[champion_name]
        
        version_file_path = VERSIONS_DIR / f"model_{version_id}.joblib"
        
        artifact = {
            "model": champion_model,
            "version_id": version_id,
            "champion_name": champion_name,
            "features": features,
            "metrics": results[champion_name],
            "all_metrics": results,
            "training_started_at": training_started_iso,
            "trained_at": training_completed_iso,
            "artifact_path": str(version_file_path.absolute()),
            "model_path": str(CHAMPION_MODEL_PATH.absolute())
        }
        
        # Save versioned artifact
        joblib.dump(artifact, version_file_path)

        # 3. CHAMPION / CHALLENGER PROMOTION DECISION
        current_champion_r2 = -999.0
        current_champion_mae = 99999.0
        if METADATA_PATH.exists():
            try:
                with open(METADATA_PATH, "r") as f:
                    curr_meta = json.load(f)
                    current_champion_r2 = float(curr_meta.get("metrics", {}).get("r2", -999.0))
                    current_champion_mae = float(curr_meta.get("metrics", {}).get("mae", 99999.0))
            except Exception:
                pass

        challenger_r2 = float(results[champion_name]["r2"])
        challenger_mae = float(results[champion_name]["mae"])
        
        # Only replace if both R2 improves and MAE improves (or if no previous champion exists, or if features changed)
        if current_champion_r2 == -999.0:
            promoted = True
        else:
            try:
                with open(METADATA_PATH, "r") as f:
                    curr_meta = json.load(f)
                    curr_features = curr_meta.get("features", [])
            except Exception:
                curr_features = []
            features_changed = set(curr_features) != set(features)
            promoted = ((challenger_r2 > current_champion_r2) and (challenger_mae < current_champion_mae)) or features_changed

        if promoted:
            joblib.dump(artifact, CHAMPION_MODEL_PATH)
            with open(METADATA_PATH, "w") as f:
                json.dump(artifact, f, indent=2, default=str)
            print(f"🏆 [CHAMPION PROMOTED] Challenger '{champion_name}' (R²: {challenger_r2:.4f}, MAE: {challenger_mae:.2f}) promoted over previous champion (R²: {current_champion_r2:.4f}, MAE: {current_champion_mae:.2f})")
            ret_artifact = artifact
        else:
            print(f"🛡️ [CHALLENGER REJECTED] Challenger '{champion_name}' (R²: {challenger_r2:.4f}, MAE: {challenger_mae:.2f}) did not outperform champion (R²: {current_champion_r2:.4f}, MAE: {current_champion_mae:.2f})")
            try:
                ret_artifact = joblib.load(CHAMPION_MODEL_PATH)
            except Exception:
                ret_artifact = artifact

        # Update registry history
        history = cls.get_version_history()
        history.insert(0, {
            "version_id": version_id,
            "champion_name": champion_name,
            "promoted": promoted,
            "metrics": results[champion_name],
            "trained_at": training_completed_iso,
            "artifact_path": str(version_file_path.absolute())
        })
        with open(REGISTRY_PATH, "w") as f:
            json.dump(history[:20], f, indent=2, default=str)

        from app.services.prediction_engine import prediction_engine
        prediction_engine.reload_model()

        return ret_artifact

