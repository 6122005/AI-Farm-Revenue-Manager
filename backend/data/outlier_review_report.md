# Outlier Review Report: Suspicious Low-Price Bookings

The following bookings were flagged as abnormally low-priced during data preprocessing and were excluded from training to prevent model bias.

| Row Index | Date | Commercial Slot | Guests | Actual Price | Expected Range | Reason |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| 161 | 2024-06-28 | 12H Day | 4 | ₹700 | ₹1,500 – ₹4,500 | Actual price ₹700 is abnormally low compared to the segment median of ₹2,500 (typical for 12H Day on weekends if is_weekend=0). |
| 192 | 2024-08-14 | 12H Day | 12 | ₹500 | ₹1,500 – ₹4,500 | Actual price ₹500 is abnormally low compared to the segment median of ₹2,500 (typical for 12H Day on weekends if is_weekend=0). |
| 199 | 2024-08-24 | 12H Day | 4 | ₹500 | ₹1,410 – ₹4,230 | Actual price ₹500 is abnormally low compared to the segment median of ₹2,350 (typical for 12H Day on weekends if is_weekend=1). |
| 352 | 2025-03-26 | 12H Day | 4 | ₹1,000 | ₹1,800 – ₹5,400 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹3,000 (typical for 12H Day on weekends if is_weekend=0). |
| 450 | 2025-06-30 | 12H Day | 4 | ₹500 | ₹1,500 – ₹4,500 | Actual price ₹500 is abnormally low compared to the segment median of ₹2,500 (typical for 12H Day on weekends if is_weekend=0). |
| 467 | 2025-07-22 | 12H Day | 12 | ₹700 | ₹1,350 – ₹4,050 | Actual price ₹700 is abnormally low compared to the segment median of ₹2,250 (typical for 12H Day on weekends if is_weekend=0). |
| 485 | 2025-08-16 | 24H Day | 10 | ₹1,000 | ₹2,700 – ₹8,100 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹4,500 (typical for 24H Day on weekends if is_weekend=1). |
| 490 | 2025-08-23 | 12H Day | 4 | ₹500 | ₹1,410 – ₹4,230 | Actual price ₹500 is abnormally low compared to the segment median of ₹2,350 (typical for 12H Day on weekends if is_weekend=1). |
| 512 | 2025-09-20 | 24H Day | 10 | ₹1,000 | ₹2,400 – ₹7,200 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹4,000 (typical for 24H Day on weekends if is_weekend=1). |
| 552 | 2025-11-08 | 24H Day | 15 | ₹1,000 | ₹3,000 – ₹9,000 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹5,000 (typical for 24H Day on weekends if is_weekend=1). |
| 579 | 2025-12-27 | 24H Day | 10 | ₹500 | ₹2,790 – ₹8,370 | Actual price ₹500 is abnormally low compared to the segment median of ₹4,650 (typical for 24H Day on weekends if is_weekend=1). |
| 587 | 2026-01-11 | 24H Day | 10 | ₹1,000 | ₹3,000 – ₹9,000 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹5,000 (typical for 24H Day on weekends if is_weekend=1). |
| 594 | 2026-01-23 | 24H Day | 10 | ₹1,000 | ₹2,400 – ₹7,200 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹4,000 (typical for 24H Day on weekends if is_weekend=0). |
| 666 | 2026-04-26 | 12H Day | 10 | ₹1,000 | ₹2,400 – ₹7,200 | Actual price ₹1,000 is abnormally low compared to the segment median of ₹4,000 (typical for 12H Day on weekends if is_weekend=1). |
