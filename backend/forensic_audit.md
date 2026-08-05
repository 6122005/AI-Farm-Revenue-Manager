# Forensic Audit Summary

## The Incident
The system produced an impossible discrepancy in evaluations:
- Pipeline A (Offline Experiment): MAE ₹330
- Pipeline B (Online Replay): MAE ₹7264

This audit proves that the ML engine and model weights are fully sound. The issue is strictly an inference pipeline data transformation failure. 

## Investigation Steps Performed
1. **Identical Model Verification:** Verified that `champion_model.joblib` trained offline is exactly the same model used in online inference.
2. **Feature Extraction Trace:** Scripted `scratch_forensic_incident_audit.py` to trace the entire feature transformation process for 30 historical bookings across both pipelines.
3. **Difference Highlighting:** Extracted the differences in exact feature values into `feature_diff.csv`.
4. **Prediction Trace:** Compared the raw model outputs (log transformed prices) to the `np.expm1()` prices in `prediction_diff.csv`.

## Conclusion
During inference, the model is being evaluated on a 1-row DataFrame. Because the historical context is not properly joined with this row *before* feature extraction, **all time-series and hierarchical rolling features evaluate to their default fallback states (0.0 or 8500.0).** 

The model is effectively blind during inference, making predictions based only on the raw day-of-week and month, leading to the massive drop in accuracy. 

Please review the complete trace in `pipeline_trace.md` and the fix proposal in `root_cause_report.md`.
