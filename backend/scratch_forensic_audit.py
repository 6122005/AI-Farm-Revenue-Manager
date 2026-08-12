import pandas as pd
import numpy as np
import shap
from pathlib import Path
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
import warnings
import json
import logging
warnings.filterwarnings('ignore')

# Suppress debug logs
logging.getLogger().setLevel(logging.ERROR)

from app.services.data_pipeline import DataPipeline
from app.services.ml_trainer import MLTrainer
from app.services.feature_engineering import FeatureEngineer

def safe_mape(y_true, y_pred):
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask]))

def run_audit():
    print("="*50)
    print("STEP 1: DATASET FORENSIC AUDIT")
    print("="*50)
    file_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
    excel_file = pd.ExcelFile(file_path)
    print(f"Sheet names: {excel_file.sheet_names}")
    
    raw_df = pd.read_excel(file_path, sheet_name='Events Export')
    print(f"Row count: {len(raw_df)}")
    print(f"Column count: {len(raw_df.columns)}")
    print(f"Missing values:\n{raw_df.isnull().sum()[raw_df.isnull().sum() > 0].to_string()}")
    print(f"Duplicate rows: {raw_df.duplicated().sum()}")
    
    # Process through pipeline to get clean dataframe
    df_clean = DataPipeline.process_with_explicit_mapping(
        file_path,
        price_col="Rate",
        date_col="Start Date",
        slot_col="Booking Category",
        guests_col="person_count",
        lead_col="Lead Days",
        competitor_col="Competitor_Price"
    )
    print(f"Processed row count: {len(df_clean)}")
    
    if "outlier" in df_clean.columns:
        outlier_count = df_clean["outlier"].sum()
        print(f"\nOutliers marked: {outlier_count} ({(outlier_count/len(df_clean))*100:.2f}%)")
        outlier_df = df_clean[df_clean["outlier"] == True]
        if len(outlier_df) > 0:
            print(f"Outlier Price Median: {outlier_df['selling_price'].median()}")
            print(f"Outlier slots:\n{outlier_df['commercial_slot'].value_counts().head(3).to_string()}")
    else:
        print("\n'outlier' column not found in processed dataframe.")

    print("\n" + "="*50)
    print("STEP 2: VERIFY WEEKEND DATA")
    print("="*50)
    # df_clean has booking_date and is_weekend
    df_clean['booking_date_dt'] = pd.to_datetime(df_clean['booking_date'])
    df_clean['calendar_weekend'] = df_clean['booking_date_dt'].dt.dayofweek >= 5
    df_clean['weekend_conflict'] = df_clean['calendar_weekend'] != df_clean['is_weekend'].astype(bool)
    conflicts = df_clean['weekend_conflict'].sum()
    print(f"Total conflicts: {conflicts} ({(conflicts/len(df_clean))*100:.2f}%)")
    
    print("\n" + "="*50)
    print("STEP 6: CURRENT MODEL BASELINE")
    print("="*50)
    features = FeatureEngineer.create_features(df_clean)
    target = 'selling_price'
    
    # Exclude outliers for baseline
    train_df = features[features.get('outlier', False) == False] if 'outlier' in features.columns else features
    
    X = train_df.drop(columns=[target, 'booking_date', 'booking_date_dt', 'commercial_slot', 'outlier', 'weekend_conflict', 'calendar_weekend'], errors='ignore')
    
    # Remove any non-numeric columns
    X = X.select_dtypes(include=[np.number])
    y = train_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    base_model = xgb.XGBRegressor(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42
    )
    base_model.fit(X_train, y_train)
    y_pred = base_model.predict(X_test)
    
    base_r2 = r2_score(y_test, y_pred)
    base_mae = mean_absolute_error(y_test, y_pred)
    base_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    base_mape = safe_mape(y_test, y_pred)
    
    print(f"Random Split R²: {base_r2:.4f}")
    print(f"Random Split MAE: ₹{base_mae:.2f}")
    print(f"Random Split RMSE: ₹{base_rmse:.2f}")
    print(f"Random Split MAPE: {base_mape*100:.2f}%")
    
    print("\n" + "="*50)
    print("STEP 17: VALIDATION METHODOLOGY (TIME-BASED)")
    print("="*50)
    # Sort by date for time-based split
    train_df_sorted = train_df.sort_values('booking_date_dt')
    X_time = train_df_sorted[X.columns]
    y_time = train_df_sorted[target]
    
    split_idx = int(len(X_time) * 0.8)
    X_train_t, X_test_t = X_time.iloc[:split_idx], X_time.iloc[split_idx:]
    y_train_t, y_test_t = y_time.iloc[:split_idx], y_time.iloc[split_idx:]
    
    time_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    time_model.fit(X_train_t, y_train_t)
    y_pred_t = time_model.predict(X_test_t)
    
    time_r2 = r2_score(y_test_t, y_pred_t)
    time_mae = mean_absolute_error(y_test_t, y_pred_t)
    print(f"Time-based R²: {time_r2:.4f}")
    print(f"Time-based MAE: ₹{time_mae:.2f}")

    print("\n" + "="*50)
    print("STEP 7: FEATURE IMPORTANCE")
    print("="*50)
    importances = base_model.feature_importances_
    feat_imp = pd.DataFrame({'Feature': X.columns, 'Importance': importances}).sort_values('Importance', ascending=False)
    print(feat_imp.head(10).to_string(index=False))
    
    print("\n" + "="*50)
    print("STEP 8: FEATURE ABLATION STUDY")
    print("="*50)
    
    groups = {
        "Month": [c for c in X.columns if 'month' in c.lower()],
        "Weekend": [c for c in X.columns if 'weekend' in c.lower()],
        "Duration": [c for c in X.columns if 'duration' in c.lower()],
        "Guest": [c for c in X.columns if 'person' in c.lower() or 'guest' in c.lower()],
        "Lead Days": [c for c in X.columns if 'lead' in c.lower()],
        "Historical Pricing": [c for c in X.columns if 'avg' in c.lower() or 'med' in c.lower() or 'hist' in c.lower()]
    }
    
    for g_name, g_cols in groups.items():
        if not g_cols:
            continue
        X_abl = X_time.drop(columns=g_cols, errors='ignore')
        X_train_a, X_test_a = X_abl.iloc[:split_idx], X_abl.iloc[split_idx:]
        abl_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        abl_model.fit(X_train_a, y_train_t)
        y_pred_a = abl_model.predict(X_test_a)
        abl_r2 = r2_score(y_test_t, y_pred_a)
        print(f"{g_name:20s} | Base: {time_r2:.4f} | Ablated: {abl_r2:.4f} | Diff: {time_r2 - abl_r2:.4f}")

    print("\n" + "="*50)
    print("STEP 10 & 11: SEGMENT PERFORMANCE & WORST ERROR SEGMENTS")
    print("="*50)
    # We will use the time-based predictions
    test_results = X_test_t.copy()
    test_results['Actual'] = y_test_t
    test_results['Predicted'] = y_pred_t
    test_results['Error'] = np.abs(test_results['Actual'] - test_results['Predicted'])
    
    test_results['Month'] = train_df_sorted.iloc[split_idx:]['month']
    test_results['Slot'] = train_df_sorted.iloc[split_idx:]['commercial_slot']
    test_results['Weekend'] = train_df_sorted.iloc[split_idx:]['is_weekend']
    
    segment_err = test_results.groupby(['Month', 'Slot', 'Weekend']).agg(
        MAE=('Error', 'mean'),
        Count=('Error', 'count')
    ).reset_index()
    
    worst_segments = segment_err[segment_err['Count'] > 2].sort_values('MAE', ascending=False).head(5)
    print("Worst Month/Slot/Weekend segments:")
    print(worst_segments.to_string(index=False))
    
    print("\n" + "="*50)
    print("STEP 19: MODEL COMPARISON")
    print("="*50)
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train_t, y_train_t)
    rf_r2 = r2_score(y_test_t, rf.predict(X_test_t))
    
    ridge = Ridge()
    ridge.fit(X_train_t, y_train_t)
    ridge_r2 = r2_score(y_test_t, ridge.predict(X_test_t))
    
    print(f"XGBoost R²:       {time_r2:.4f}")
    print(f"Random Forest R²: {rf_r2:.4f}")
    print(f"Ridge R²:         {ridge_r2:.4f}")

if __name__ == "__main__":
    run_audit()
