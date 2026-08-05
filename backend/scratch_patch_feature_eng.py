import sys
from pathlib import Path

# We will modify feature_engineering.py
file_path = "app/services/feature_engineering.py"
with open(file_path, "r") as f:
    content = f.read()

import re

# Find process_dataframe definition
old_def = "    def process_dataframe(cls, df: pd.DataFrame, is_prediction: bool = False) -> pd.DataFrame:"
new_def = "    def process_dataframe(cls, df: pd.DataFrame, is_prediction: bool = False, historical_df=None) -> pd.DataFrame:"
content = content.replace(old_def, new_def)

# Add strict rolling features calculation at the end of process_dataframe
# just before returning combined_df
old_return = "        return combined_df"
new_return = """        # Add Strict Rolling Features
        if historical_df is not None and not historical_df.empty:
            ref_df = historical_df.copy()
            ref_df['booking_date'] = pd.to_datetime(ref_df['booking_date'])
            ref_df = ref_df.sort_values('booking_date')
            global_median = ref_df['selling_price'].median()
        else:
            ref_df = pd.DataFrame()
            global_median = 8500.0

        if 'booking_date' in combined_df.columns:
            combined_df['booking_date_dt'] = pd.to_datetime(combined_df['booking_date'])
        else:
            combined_df['booking_date_dt'] = pd.to_datetime('today')

        density_col = []
        momentum_col = []
        variance_col = []
        
        for i, row in combined_df.iterrows():
            b_date = row['booking_date_dt']
            slot = row.get('commercial_slot', '12H Day')
            
            if not ref_df.empty:
                past_bookings = ref_df[ref_df['booking_date'] < b_date]
                sim_past = past_bookings[past_bookings['commercial_slot'] == slot]
                
                window_start = b_date - pd.Timedelta(days=30)
                sim_30d = sim_past[sim_past['booking_date'] >= window_start]
                
                density_col.append(len(sim_30d))
                
                if len(sim_30d) > 0:
                    momentum_col.append(sim_30d['selling_price'].mean())
                else:
                    # Fallback to historical expanding median to prevent target leakage
                    if len(past_bookings) > 0:
                        momentum_col.append(past_bookings['selling_price'].median())
                    else:
                        momentum_col.append(global_median)
                        
                if len(sim_past) > 1:
                    variance_col.append(sim_past['selling_price'].std())
                else:
                    variance_col.append(0)
            else:
                density_col.append(0)
                momentum_col.append(global_median)
                variance_col.append(0)

        combined_df['similar_booking_density_30d'] = density_col
        combined_df['price_momentum_30d'] = momentum_col
        combined_df['historical_variance'] = variance_col
        
        if 'days_before_festival' in combined_df.columns:
            combined_df['is_near_holiday'] = (combined_df['days_before_festival'] <= 3).astype(int)
        else:
            combined_df['is_near_holiday'] = 0

        combined_df = combined_df.drop(columns=['booking_date_dt'], errors='ignore')

        return combined_df"""

content = content.replace(old_return, new_return)

with open(file_path, "w") as f:
    f.write(content)

print("Patched feature_engineering.py")
