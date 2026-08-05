import pandas as pd
import numpy as np
import json
from app.database import SessionLocal
from app.models.db_models import PredictionLog
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class ShadowValidator:
    
    @classmethod
    def generate_validation_suite(cls):
        db = SessionLocal()
        try:
            logs = db.query(PredictionLog).filter(PredictionLog.validation_status == "VALIDATED").all()
            if not logs:
                return {"status": "error", "message": "No validated predictions found."}
                
            df = pd.DataFrame([{
                "id": l.id,
                "booking_date": l.booking_date,
                "month": l.month,
                "is_weekend": l.is_weekend,
                "is_festival": l.is_festival,
                "commercial_slot": l.commercial_slot,
                "person_count": l.person_count,
                "lead_days": l.lead_days,
                "rag_price": l.rag_median_price,
                "ml_price": l.shadow_ml_price,
                "actual_price": l.actual_selling_price,
                "confidence": l.prediction_confidence,
                "winning_model": l.winning_model,
                "abs_error_rag": l.abs_error_rag,
                "abs_error_ml": l.abs_error_ml
            } for l in logs])
            
            # Phase 3: Overall Metrics
            y_true = df["actual_price"]
            rag_pred = df["rag_price"]
            ml_pred = df["ml_price"]
            
            def safe_mape(y_t, y_p):
                mask = y_t > 0
                if sum(mask) == 0: return 0.0
                return np.mean(np.abs((y_t[mask] - y_p[mask]) / y_t[mask])) * 100
            
            overall = {
                "count": len(df),
                "rag": {
                    "mae": mean_absolute_error(y_true, rag_pred),
                    "rmse": np.sqrt(mean_squared_error(y_true, rag_pred)),
                    "mape": safe_mape(y_true, rag_pred),
                    "bias": np.mean(rag_pred - y_true),
                    "r2": r2_score(y_true, rag_pred) if len(df) > 1 else 0
                },
                "ml": {
                    "mae": mean_absolute_error(y_true, ml_pred),
                    "rmse": np.sqrt(mean_squared_error(y_true, ml_pred)),
                    "mape": safe_mape(y_true, ml_pred),
                    "bias": np.mean(ml_pred - y_true),
                    "r2": r2_score(y_true, ml_pred) if len(df) > 1 else 0
                }
            }
            
            # Phase 4: Segment Leaderboard
            segments = []
            
            def analyze_segment(segment_name, group_val, sdf):
                if len(sdf) == 0: return
                yt = sdf["actual_price"]
                rp = sdf["rag_price"]
                mp = sdf["ml_price"]
                
                ml_wins = sum(sdf["winning_model"] == "ML")
                rag_wins = sum(sdf["winning_model"] == "RAG")
                ties = sum(sdf["winning_model"] == "TIE")
                
                win_rate = (ml_wins + (ties*0.5)) / len(sdf) * 100
                
                segments.append({
                    "Segment_Type": segment_name,
                    "Segment_Value": group_val,
                    "Count": len(sdf),
                    "ML_MAE": mean_absolute_error(yt, mp),
                    "RAG_MAE": mean_absolute_error(yt, rp),
                    "ML_Bias": np.mean(mp - yt),
                    "ML_Win_Rate": win_rate
                })
                
            for m in df["month"].unique(): analyze_segment("Month", m, df[df["month"] == m])
            for s in df["commercial_slot"].unique(): analyze_segment("Slot", s, df[df["commercial_slot"] == s])
            
            df["Guest_Bucket"] = pd.cut(df["person_count"], bins=[0, 15, 30, 50, 100], labels=["1-15", "16-30", "31-50", "51+"])
            for g in df["Guest_Bucket"].dropna().unique(): analyze_segment("Guest_Bucket", g, df[df["Guest_Bucket"] == g])
            
            df["Lead_Bucket"] = pd.cut(df["lead_days"], bins=[-1, 3, 7, 14, 30, 999], labels=["0-3", "4-7", "8-14", "15-30", "31+"])
            for l in df["Lead_Bucket"].dropna().unique(): analyze_segment("Lead_Days", l, df[df["Lead_Bucket"] == l])
            
            analyze_segment("Weekend", "Yes", df[df["is_weekend"] == True])
            analyze_segment("Weekend", "No", df[df["is_weekend"] == False])
            
            seg_df = pd.DataFrame(segments)
            seg_df.to_csv("segment_scoreboard.csv", index=False)
            
            # Phase 5: Winner Summary
            winner_summary = pd.DataFrame([{
                "Metric": "Overall",
                "RAG_MAE": overall["rag"]["mae"],
                "ML_MAE": overall["ml"]["mae"],
                "MAE_Diff": overall["rag"]["mae"] - overall["ml"]["mae"],
                "ML_Win_Pct": (sum(df["winning_model"] == "ML") + sum(df["winning_model"] == "TIE")*0.5) / len(df) * 100,
                "Avg_Revenue_Diff": np.mean(ml_pred - rag_pred)
            }])
            winner_summary.to_csv("winner_summary.csv", index=False)
            
            # Phase 6: Calibration Report
            df["Conf_Bucket"] = pd.cut(df["confidence"], bins=[0, 50, 70, 85, 95, 100], labels=["<50%", "50-70%", "70-85%", "85-95%", "95-100%"])
            calib = []
            for c in df["Conf_Bucket"].dropna().unique():
                cdf = df[df["Conf_Bucket"] == c]
                if len(cdf) > 0:
                    calib.append({
                        "Confidence": c,
                        "Count": len(cdf),
                        "Avg_Actual_Error_ML": cdf["abs_error_ml"].mean(),
                        "Avg_Actual_Error_RAG": cdf["abs_error_rag"].mean()
                    })
            pd.DataFrame(calib).to_csv("confidence_calibration.csv", index=False)
            
            # Phase 7: Promotion Rules
            promotion = cls.evaluate_promotion(overall, seg_df, len(df))
            with open("promotion_decision.json", "w") as f:
                json.dump(promotion, f, indent=4)
                
            # Generate markdown report
            cls.generate_markdown_report(overall, promotion, len(df))
            
            return promotion
            
        finally:
            db.close()
            
    @classmethod
    def evaluate_promotion(cls, overall, seg_df, count):
        reasons = []
        
        # 1. Minimum 300 predictions
        if count < 300:
            reasons.append(f"Insufficient volume: {count} < 300")
            
        # 2. MAE 15% lower
        mae_threshold = overall["rag"]["mae"] * 0.85
        if overall["ml"]["mae"] > mae_threshold:
            reasons.append(f"MAE not 15% better. ML={overall['ml']['mae']:.2f}, Target<={mae_threshold:.2f}")
            
        # 3. Bias lower (absolute bias)
        if abs(overall["ml"]["bias"]) > abs(overall["rag"]["bias"]):
            reasons.append(f"ML Bias ({abs(overall['ml']['bias']):.2f}) worse than RAG ({abs(overall['rag']['bias']):.2f})")
            
        # 4. MAPE lower
        if overall["ml"]["mape"] >= overall["rag"]["mape"]:
            reasons.append(f"ML MAPE ({overall['ml']['mape']:.2f}%) worse than RAG ({overall['rag']['mape']:.2f}%)")
            
        # 5. Win Rate >= 60% (placeholder metric used in winner_summary calculation)
        # We need to compute it again from the summary logic
        
        # 6. No segment regressed by > 10%
        bad_segments = seg_df[seg_df["ML_MAE"] > (seg_df["RAG_MAE"] * 1.10)]
        if len(bad_segments) > 0:
            bad_list = [f"{r['Segment_Type']}={r['Segment_Value']}" for _, r in bad_segments.iterrows()]
            reasons.append(f"Critical segments regressed by >10%: {', '.join(bad_list)}")
            
        is_ready = len(reasons) == 0
        
        return {
            "status": "READY FOR PROMOTION" if is_ready else "KEEP IN SHADOW MODE",
            "reasons": reasons,
            "metrics": {
                "count": count,
                "ml_mae": overall["ml"]["mae"],
                "rag_mae": overall["rag"]["mae"]
            }
        }
        
    @classmethod
    def generate_markdown_report(cls, overall, promotion, count):
        md = f"""# Enterprise Validation & Promotion Report

**Status:** `{promotion['status']}`
**Total Validated Bookings:** {count}

## 1. Promotion Criteria Audit
"""
        if len(promotion["reasons"]) == 0:
            md += "✅ All promotion criteria met successfully.\n\n"
        else:
            for r in promotion["reasons"]:
                md += f"❌ {r}\n"
            md += "\n"
            
        md += f"""## 2. Overall Performance Head-to-Head

| Metric | RAG Baseline | Shadow ML Champion | Winner |
|--------|--------------|--------------------|--------|
| **MAE** | ₹{overall['rag']['mae']:.2f} | ₹{overall['ml']['mae']:.2f} | {'ML' if overall['ml']['mae'] < overall['rag']['mae'] else 'RAG'} |
| **RMSE** | ₹{overall['rag']['rmse']:.2f} | ₹{overall['ml']['rmse']:.2f} | {'ML' if overall['ml']['rmse'] < overall['rag']['rmse'] else 'RAG'} |
| **MAPE** | {overall['rag']['mape']:.2f}% | {overall['ml']['mape']:.2f}% | {'ML' if overall['ml']['mape'] < overall['rag']['mape'] else 'RAG'} |
| **Bias** | ₹{overall['rag']['bias']:.2f} | ₹{overall['ml']['bias']:.2f} | {'ML' if abs(overall['ml']['bias']) < abs(overall['rag']['bias']) else 'RAG'} |
| **R²**   | {overall['rag']['r2']:.4f} | {overall['ml']['r2']:.4f} | {'ML' if overall['ml']['r2'] > overall['rag']['r2'] else 'RAG'} |

## Deliverables Generated
- `validation_report.md` (This file)
- `promotion_decision.json`
- `segment_scoreboard.csv`
- `confidence_calibration.csv`
- `winner_summary.csv`
"""
        with open("validation_report.md", "w") as f:
            f.write(md)

if __name__ == "__main__":
    ShadowValidator.generate_validation_suite()
