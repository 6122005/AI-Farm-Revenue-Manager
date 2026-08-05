# Enterprise Validation & Promotion Report

**Status:** `KEEP IN SHADOW MODE`
**Total Validated Bookings:** 138

## 1. Promotion Criteria Audit
❌ Insufficient volume: 138 < 300
❌ MAE not 15% better. ML=7264.61, Target<=7160.08

## 2. Overall Performance Head-to-Head

| Metric | RAG Baseline | Shadow ML Champion | Winner |
|--------|--------------|--------------------|--------|
| **MAE** | ₹8423.62 | ₹7264.61 | ML |
| **RMSE** | ₹8882.31 | ₹7976.36 | ML |
| **MAPE** | 73.77% | 61.29% | ML |
| **Bias** | ₹-8423.62 | ₹-7264.61 | ML |
| **R²**   | -6.2748 | -4.8665 | ML |

## Deliverables Generated
- `validation_report.md` (This file)
- `promotion_decision.json`
- `segment_scoreboard.csv`
- `confidence_calibration.csv`
- `winner_summary.csv`
