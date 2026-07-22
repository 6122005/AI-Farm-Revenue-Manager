import pandas as pd
import numpy as np
from scipy.stats import ks_2samp, chi2_contingency
from typing import Dict, Any, List
from pathlib import Path

class DataDriftDetector:
    def __init__(self, threshold: float = 0.25):
        self.threshold = threshold

    def detect_drift(self, reference_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compares current uploaded dataset against reference training dataset.
        Evaluates Kolmogorov-Smirnov distance for numerical features and Chi-Square for categorical features.
        """
        if reference_df.empty or current_df.empty:
            return {
                "drift_detected": False,
                "overall_drift_score": 0.0,
                "drifted_features": [],
                "details": {},
                "recommendation": "DATASET_STABLE"
            }

        num_features = ["selling_price", "person_count", "lead_days"]
        cat_features = ["commercial_slot", "is_weekend"]

        drifted_features = []
        feature_details = {}
        total_p_val = 0.0
        feature_count = 0

        for col in num_features:
            if col in reference_df.columns and col in current_df.columns:
                ref_col = pd.to_numeric(reference_df[col], errors='coerce').dropna()
                cur_col = pd.to_numeric(current_df[col], errors='coerce').dropna()
                
                if len(ref_col) > 5 and len(cur_col) > 5:
                    ks_stat, p_val = ks_2samp(ref_col, cur_col)
                    is_drifted = bool(p_val < 0.05 or ks_stat > self.threshold)
                    feature_details[col] = {
                        "ks_stat": round(float(ks_stat), 4),
                        "p_value": round(float(p_val), 4),
                        "is_drifted": is_drifted
                    }
                    if is_drifted:
                        drifted_features.append(col)
                    total_p_val += (1.0 - p_val)
                    feature_count += 1

        for col in cat_features:
            if col in reference_df.columns and col in current_df.columns:
                try:
                    ref_counts = reference_df[col].value_counts()
                    cur_counts = current_df[col].value_counts()
                    cont_table = pd.concat([ref_counts, cur_counts], axis=1).fillna(0)
                    chi2, p_val, _, _ = chi2_contingency(cont_table)
                    is_drifted = bool(p_val < 0.05)
                    feature_details[col] = {
                        "chi2_stat": round(float(chi2), 4),
                        "p_value": round(float(p_val), 4),
                        "is_drifted": is_drifted
                    }
                    if is_drifted:
                        drifted_features.append(col)
                    total_p_val += (1.0 - p_val)
                    feature_count += 1
                except Exception:
                    pass

        overall_score = round(float(total_p_val / feature_count), 4) if feature_count > 0 else 0.0
        drift_detected = len(drifted_features) > 0 or overall_score > 0.40

        return {
            "drift_detected": drift_detected,
            "overall_drift_score": overall_score,
            "drifted_features": drifted_features,
            "details": feature_details,
            "recommendation": "RETRAINING_RECOMMENDED" if drift_detected else "DATASET_STABLE"
        }

drift_detector = DataDriftDetector()
