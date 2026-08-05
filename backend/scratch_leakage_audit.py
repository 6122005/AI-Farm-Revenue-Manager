import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

sys.path.append(str(Path(__file__).parent.parent))

from app.services.prediction_engine import prediction_engine
from app.services.feature_engineering import FeatureEngineer

def compute_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)
    bias = np.mean(y_pred - y_true)
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape, "R2": r2, "Bias": bias}

def get_base_features(df):
    f_df = FeatureEngineer.process_dataframe(df, is_prediction=False)
    cat_cols = ["slot_type", "season", "weather_condition", "month", "day_of_week"]
    f_df = pd.get_dummies(f_df, columns=[c for c in cat_cols if c in f_df.columns], dummy_na=False)
    return f_df

def add_strict_rolling_features(df):
    df = df.copy()
    df['booking_date'] = pd.to_datetime(df['booking_date'])
    df = df.sort_values('booking_date').reset_index(drop=True)
    
    # Pre-calculate global medians for fillna to avoid target leakage
    # Calculate expanding median of selling_price strictly BEFORE each row
    expanding_median = []
    current_prices = []
    for i, row in df.iterrows():
        if len(current_prices) > 0:
            expanding_median.append(np.median(current_prices))
        else:
            expanding_median.append(0) # or some base floor
        current_prices.append(row['selling_price'])
    df['expanding_global_median'] = expanding_median
    
    density_col = []
    momentum_col = []
    variance_col = []
    
    for i, row in df.iterrows():
        b_date = row['booking_date']
        
        # STRICT LEAKAGE PREVENTION: Only look at data STRICTLY BEFORE the current booking_date
        past_bookings = df[df['booking_date'] < b_date]
        sim_past = past_bookings[past_bookings['commercial_slot'] == row['commercial_slot']]
        
        # 30-day window for density and momentum
        window_start = b_date - pd.Timedelta(days=30)
        sim_30d = sim_past[sim_past['booking_date'] >= window_start]
        
        # Density
        density_col.append(len(sim_30d))
        
        # Momentum
        if len(sim_30d) > 0:
            momentum_col.append(sim_30d['selling_price'].mean())
        else:
            # NO TARGET LEAKAGE. Fallback to expanding global median, NOT row['selling_price']
            momentum_col.append(row['expanding_global_median'])
            
        # Variance
        if len(sim_past) > 1:
            variance_col.append(sim_past['selling_price'].std())
        else:
            variance_col.append(0)
            
    df['similar_booking_density_30d'] = density_col
    df['price_momentum_30d'] = momentum_col
    df['historical_variance'] = variance_col
    
    # Holiday Distance (assuming days_before_festival exists from base feature engineer)
    if 'days_before_festival' in df.columns:
        df['is_near_holiday'] = (df['days_before_festival'] <= 3).astype(int)
    else:
        df['is_near_holiday'] = 0
        
    return df

def main():
    print("Loading data...")
    raw_df = prediction_engine.get_clean_data()
    raw_df = raw_df.sort_values('booking_date').reset_index(drop=True)
    
    # Add strict rolling features FIRST (before dropping cols)
    print("Adding strict point-in-time features...")
    df_with_rolling = add_strict_rolling_features(raw_df)
    
    print("Extracting base features...")
    df_all_features = get_base_features(df_with_rolling)
    
    drop_cols = ["id", "booking_id", "booking_date", "check_in_date", "check_out_date", "status", "platform", "selling_price", "commercial_slot", "festival_name"]
    target = "selling_price"
    
    def prep_xy(df, features_to_keep=None):
        cols_to_drop = [c for c in drop_cols if c in df.columns]
        X = df.drop(columns=cols_to_drop)
        if features_to_keep:
            available = [f for f in features_to_keep if f in X.columns]
            X = X[available]
        else:
            # Select only numeric/bool
            X = X.select_dtypes(include=['int', 'float', 'bool', 'uint8', 'int64', 'float64'])
            
        for c in X.columns:
            if X[c].dtype == bool:
                X[c] = X[c].astype(int)
        y = df[target]
        return X, y

    # Define feature groups for strict ablation
    base_X, base_y = prep_xy(df_all_features)
    # Remove our new features from base to get true baseline
    new_cols = ['similar_booking_density_30d', 'price_momentum_30d', 'historical_variance', 'is_near_holiday', 'expanding_global_median']
    base_feat_list = [c for c in base_X.columns if c not in new_cols]
    
    X_base = base_X[base_feat_list]
    
    # Ablation
    results = {}
    model = XGBRegressor(random_state=42, n_jobs=-1)
    
    def eval_subset(X_sub, y_sub):
        tscv = TimeSeriesSplit(n_splits=5)
        metrics = []
        for train_index, test_index in tscv.split(X_sub):
            X_train, X_test = X_sub.iloc[train_index], X_sub.iloc[test_index]
            y_train, y_test = y_sub.iloc[train_index], y_sub.iloc[test_index]
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics.append(compute_metrics(y_test, preds))
        return {k: np.mean([m[k] for m in metrics]) for k in metrics[0].keys()}

    print("Evaluating Baseline...")
    results["Baseline (No Leaks)"] = eval_subset(X_base, base_y)
    
    print("Evaluating + Density...")
    X_d = base_X[base_feat_list + ['similar_booking_density_30d']]
    results["+ Booking Density"] = eval_subset(X_d, base_y)
    
    print("Evaluating + Momentum...")
    X_dm = base_X[base_feat_list + ['similar_booking_density_30d', 'price_momentum_30d']]
    results["+ Price Momentum"] = eval_subset(X_dm, base_y)
    
    print("Evaluating + Variance...")
    X_dmv = base_X[base_feat_list + ['similar_booking_density_30d', 'price_momentum_30d', 'historical_variance']]
    results["+ Historical Variance"] = eval_subset(X_dmv, base_y)
    
    print("Evaluating All Features...")
    X_all = base_X[base_feat_list + ['similar_booking_density_30d', 'price_momentum_30d', 'historical_variance', 'is_near_holiday']]
    results["+ Holiday Dist (All)"] = eval_subset(X_all, base_y)
    
    # Report
    md = []
    md.append("# Strict Leakage Audit & Point-in-Time Ablation Study\n")
    md.append("This report explicitly addresses the risk of Target Leakage in rolling features by enforcing strict `< booking_date` filters and preventing fallback to the current row's price.\n")
    
    md.append("| Feature Set | MAE | RMSE | MAPE | R² | Bias |")
    md.append("|---|---|---|---|---|---|")
    for name, m in results.items():
        md.append(f"| {name} | ₹{m['MAE']:.2f} | ₹{m['RMSE']:.2f} | {m['MAPE']:.2f}% | {m['R2']:.4f} | ₹{m['Bias']:.2f} |")
        
    md.append("\n## Audit Conclusion")
    rag_mae = 962.40
    champ_mae = results["+ Holiday Dist (All)"]['MAE']
    
    if champ_mae < rag_mae:
        md.append(f"✅ **LEAKAGE-FREE ML BEATS RAG**: The strictly point-in-time XGBoost model achieves an MAE of ₹{champ_mae:.2f} vs RAG's ₹{rag_mae:.2f}. The extremely low ₹332 MAE previously seen was partially due to leakage in the momentum fallback. The corrected features represent true generalizable performance.")
    else:
        md.append(f"❌ **ML FAILS WITHOUT LEAKAGE**: After removing the target leakage, the ML model's MAE rose to ₹{champ_mae:.2f}, which is worse than RAG's ₹{rag_mae:.2f}. The ML model cannot currently be trusted as a primary predictor.")
        
    out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/3a59922d-8820-463a-b894-e3203ba9f13f/leakage_audit_report.md"
    with open(out_path, "w") as f:
        f.write("\n".join(md))
    print(f"Leakage Audit written to {out_path}")

if __name__ == "__main__":
    main()
