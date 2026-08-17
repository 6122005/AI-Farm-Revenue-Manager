import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from app.services.prediction_engine import prediction_engine
from app.services.ml_trainer import CATEGORICAL_COLS, NUMERICAL_COLS, BINARY_COLS
import time

class BacktestingEngine:
    """
    Simulates historical predictions using only data available prior to the booking date.
    Satisfies Product Builder Spec #35: Backtesting
    """
    
    @classmethod
    def run_historical_simulation(cls, window_size=50):
        print(f"🚀 [BACKTESTING] Starting Chronological Backtesting Simulation (Window Size: {window_size})")
        start_time = time.time()
        
        df = prediction_engine.get_clean_data()
        df = df.dropna(subset=['booking_date', 'selling_price'])
        
        # Ensure chronological order
        df = df.sort_values('booking_date').reset_index(drop=True)
        
        total_records = len(df)
        min_train_size = 150 # Need at least 150 records to train a sensible model
        
        if total_records <= min_train_size:
            print("⚠️ Not enough data for meaningful backtesting simulation.")
            return pd.DataFrame()
            
        results = []
        features = CATEGORICAL_COLS + NUMERICAL_COLS + BINARY_COLS
        
        # Simulate walking forward in time
        for i in range(min_train_size, total_records, window_size):
            # Train on data strictly BEFORE index i
            train_df = df.iloc[:i].copy()
            
            # Predict on the next 'window_size' records
            test_end = min(i + window_size, total_records)
            test_df = df.iloc[i:test_end].copy()
            
            print(f"🔄 Training on {len(train_df)} historical records to predict next {len(test_df)} bookings...")
            
            for col in features:
                if col not in train_df.columns:
                    train_df[col] = 0
                if col not in test_df.columns:
                    test_df[col] = 0
            
            X_train = train_df[features]
            y_train = train_df['selling_price']
            X_test = test_df[features]
            
            # Fast retrain for simulation
            from catboost import CatBoostRegressor
            
            X_train_clean = X_train.copy()
            X_test_clean = X_test.copy()
            
            for col in CATEGORICAL_COLS:
                X_train_clean[col] = X_train_clean[col].fillna("UNKNOWN").astype(str)
                X_test_clean[col] = X_test_clean[col].fillna("UNKNOWN").astype(str)
                
            model = CatBoostRegressor(iterations=50, depth=4, verbose=0, cat_features=CATEGORICAL_COLS)
            try:
                model.fit(X_train_clean, y_train)
                preds = model.predict(X_test_clean)
                
                for idx, (original_idx, row) in enumerate(test_df.iterrows()):
                    results.append({
                        "Date": row['booking_date'],
                        "Slot": row['commercial_slot'],
                        "Guests": row['person_count'],
                        "Actual": row['selling_price'],
                        "Predicted": preds[idx],
                        "Error": abs(row['selling_price'] - preds[idx]),
                        "Confidence": "Medium",
                        "Simulation_Train_Size": len(train_df)
                    })
            except Exception as e:
                print(f"⚠️ Error simulating window: {e}")
                
        res_df = pd.DataFrame(results)
        if not res_df.empty:
            res_df['% Error'] = (res_df['Error'] / res_df['Actual']) * 100
            mae = res_df['Error'].mean()
            print(f"✅ [BACKTESTING] Simulation Complete in {time.time() - start_time:.2f}s")
            print(f"📊 Out-of-Time Simulated MAE: ₹{mae:.2f}")
            
        return res_df

if __name__ == "__main__":
    BacktestingEngine.run_historical_simulation()
