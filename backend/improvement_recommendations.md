# Improvement Recommendations

1. **Feature Engineer Fix**: Concatenate the incoming 1-row DataFrame with the historical dataset before extracting LOO and rolling features. Expected MAE reduction: Massive (₹7000+ -> ~₹330).
2. **Business Rules Validation**: Ensure fallback values are logged correctly without polluting the core prediction metrics.
