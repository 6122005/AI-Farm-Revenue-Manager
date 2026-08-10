import os

file_path = "app/services/feature_engineering.py"
with open(file_path, "r") as f:
    content = f.read()

# careful replacements
content = content.replace("med_p = float(group[p_col].median())", "med_p = float(group[p_col].mean())")
content = content.replace('"median_price": round(med_p, 2),', '"mean_price": round(med_p, 2),')
content = content.replace('"median_premium": prem_med,', '"mean_premium": prem_med,')
content = content.replace('yearly_medians = df.groupby("year")["base_selling_price"].median()', 'yearly_medians = df.groupby("year")["base_selling_price"].mean()')
content = content.replace('def time_decay_median(group):', 'def time_decay_mean(group):')
content = content.replace('return np.median(group["cmv_base_price"])', 'return np.mean(group["cmv_base_price"])')
content = content.replace('gp_slot = df_full.groupby(["month", "is_weekend", "is_festival", "commercial_slot"])["cmv_base_price"].median().reset_index()', 'gp_slot = df_full.groupby(["month", "is_weekend", "is_festival", "commercial_slot"])["cmv_base_price"].mean().reset_index()')
content = content.replace('"median": np.median(g["cmv_base_price"]),', '"mean": np.mean(g["cmv_base_price"]),')
content = content.replace('avg_dict[f"{prefix}_median"] = float(row["median"])', 'avg_dict[f"{prefix}_mean"] = float(row["mean"])')
content = content.replace('w_med = float(np.median(prices))', 'w_med = float(np.mean(prices))')
content = content.replace('avg_dict[f"{prefix}_weighted_median"] = w_med', 'avg_dict[f"{prefix}_weighted_mean"] = w_med')
content = content.replace('segment_median = avg_dict.get(f"{prefix}_median", 8500.0)', 'segment_mean = avg_dict.get(f"{prefix}_mean", 8500.0)')
content = content.replace('segment_weighted_median = avg_dict.get(f"{prefix}_weighted_median", segment_median)', 'segment_weighted_mean = avg_dict.get(f"{prefix}_weighted_mean", segment_mean)')
content = content.replace('"segment_median": segment_median,', '"segment_mean": segment_mean,')
content = content.replace('"segment_weighted_median": segment_weighted_median,', '"segment_weighted_mean": segment_weighted_mean,')
content = content.replace("global_median = ref_df['selling_price'].median()", "global_mean = ref_df['selling_price'].mean()")
content = content.replace("global_median = 8500.0", "global_mean = 8500.0")
content = content.replace("momentum_col.append(past_bookings['selling_price'].median())", "momentum_col.append(past_bookings['selling_price'].mean())")
content = content.replace("momentum_col.append(global_median)", "momentum_col.append(global_mean)")

with open(file_path, "w") as f:
    f.write(content)
print("Updated feature_engineering.py")
