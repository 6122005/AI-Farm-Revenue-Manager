# Model Failure Analysis

Based on the audit, the pipeline is currently returning fallback values due to the 1-row DataFrame inference bug.
The rolling time-series features are failing to construct properly during single API requests.

## Top 20 Worst Segments
- **(12, '24H Night')**: MAE ₹14252.19, MAPE 76.05% (Root Cause: Missing context / Failed features)
- **(12, '24H Day')**: MAE ₹13275.62, MAPE 75.87% (Root Cause: Missing context / Failed features)
- **(1, '24H Day')**: MAE ₹12126.52, MAPE 76.46% (Root Cause: Missing context / Failed features)
- **(7, '24H Day')**: MAE ₹11848.54, MAPE 77.50% (Root Cause: Missing context / Failed features)
- **(2, '24H Night')**: MAE ₹11818.65, MAPE 73.42% (Root Cause: Missing context / Failed features)
- **(8, '24H Day')**: MAE ₹11312.03, MAPE 73.87% (Root Cause: Missing context / Failed features)
- **(1, '24H Night')**: MAE ₹11311.49, MAPE 62.32% (Root Cause: Missing context / Failed features)
- **(2, '24H Day')**: MAE ₹11201.56, MAPE 76.97% (Root Cause: Missing context / Failed features)
- **(9, '24H Day')**: MAE ₹10788.16, MAPE 74.81% (Root Cause: Missing context / Failed features)
- **(7, '24H Night')**: MAE ₹10670.32, MAPE 73.78% (Root Cause: Missing context / Failed features)
- **(6, '24H Night')**: MAE ₹10500.06, MAPE 63.68% (Root Cause: Missing context / Failed features)
- **(3, '24H Day')**: MAE ₹10171.80, MAPE 68.82% (Root Cause: Missing context / Failed features)
- **(6, '24H Day')**: MAE ₹9432.99, MAPE 65.74% (Root Cause: Missing context / Failed features)
- **(8, '24H Night')**: MAE ₹9408.03, MAPE 60.41% (Root Cause: Missing context / Failed features)
- **(3, '24H Night')**: MAE ₹9169.68, MAPE 62.37% (Root Cause: Missing context / Failed features)
- **(10, '24H Night')**: MAE ₹9161.13, MAPE 61.55% (Root Cause: Missing context / Failed features)
- **(12, '12H Night')**: MAE ₹9110.67, MAPE 69.57% (Root Cause: Missing context / Failed features)
- **(5, '12H Night')**: MAE ₹8518.30, MAPE 66.70% (Root Cause: Missing context / Failed features)
- **(11, '24H Day')**: MAE ₹8072.60, MAPE 56.10% (Root Cause: Missing context / Failed features)
- **(9, '12H Night')**: MAE ₹7892.91, MAPE 72.35% (Root Cause: Missing context / Failed features)
