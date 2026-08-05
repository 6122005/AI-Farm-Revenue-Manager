# Real Booking Data vs AI Prediction Accuracy
**Overall Accuracy (R² Score):** 0.7886 (78.86%)
**Overall Mean Absolute Error (MAE):** ₹655.53

This report takes every single historical booking from your file, runs it through the exact same engine the dashboard uses, and compares what the AI would have charged versus what you actually charged.

| Month | Slot | Day Type | Count | Avg Actual | Avg Predicted | Avg Diff | Diff % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Jan | 12H Day | Weekday | 27 | ₹2170 | ₹1978 | ₹-193 | -8.9% |
| Jan | 12H Night | Weekday | 2 | ₹2250 | ₹1912 | ₹-338 | -15.0% |
| Jan | 12H Night | Weekend | 1 | ₹3000 | ₹4238 | ₹1238 | 41.3% |
| Jan | 24H Day | Weekday | 1 | ₹1000 | ₹6505 | ₹5505 | 550.5% |
| Jan | 24H Night | Weekday | 18 | ₹3882 | ₹3940 | ₹58 | 1.5% |
| Jan | 24H Night | Weekend | 10 | ₹4550 | ₹4110 | ₹-440 | -9.7% |
| Feb | 12H Day | Weekday | 29 | ₹2152 | ₹2222 | ₹71 | 3.3% |
| Feb | 12H Night | Weekday | 3 | ₹1900 | ₹1710 | ₹-190 | -10.0% |
| Feb | 12H Night | Weekend | 1 | ₹3000 | ₹4332 | ₹1332 | 44.4% |
| Feb | 24H Night | Weekday | 10 | ₹3457 | ₹3214 | ₹-243 | -7.0% |
| Feb | 24H Night | Weekend | 6 | ₹5083 | ₹4692 | ₹-392 | -7.7% |
| Mar | 12H Day | Weekday | 19 | ₹2882 | ₹2774 | ₹-107 | -3.7% |
| Mar | 12H Night | Weekday | 3 | ₹2833 | ₹2550 | ₹-283 | -10.0% |
| Mar | 24H Day | Weekday | 2 | ₹4600 | ₹5100 | ₹500 | 10.9% |
| Mar | 24H Night | Weekday | 38 | ₹5398 | ₹4769 | ₹-630 | -11.7% |
| Mar | 24H Night | Weekend | 13 | ₹7846 | ₹6962 | ₹-885 | -11.3% |
| Apr | 12H Day | Weekday | 21 | ₹3381 | ₹3166 | ₹-215 | -6.4% |
| Apr | 12H Night | Weekday | 4 | ₹2750 | ₹2417 | ₹-333 | -12.1% |
| Apr | 24H Day | Weekday | 3 | ₹4000 | ₹3867 | ₹-133 | -3.3% |
| Apr | 24H Night | Weekday | 43 | ₹5011 | ₹4912 | ₹-99 | -2.0% |
| Apr | 24H Night | Weekend | 11 | ₹10636 | ₹9519 | ₹-1117 | -10.5% |
| May | 12H Day | Weekday | 17 | ₹3474 | ₹3130 | ₹-344 | -9.9% |
| May | 12H Night | Weekday | 7 | ₹3286 | ₹2906 | ₹-380 | -11.6% |
| May | 24H Night | Weekday | 60 | ₹5418 | ₹5188 | ₹-230 | -4.2% |
| May | 24H Night | Weekend | 14 | ₹12393 | ₹11154 | ₹-1239 | -10.0% |
| Jun | 12H Day | Weekday | 23 | ₹3091 | ₹3796 | ₹705 | 22.8% |
| Jun | 12H Night | Weekday | 6 | ₹2167 | ₹1950 | ₹-217 | -10.0% |
| Jun | 12H Night | Weekend | 2 | ₹3000 | ₹2550 | ₹-450 | -15.0% |
| Jun | 24H Night | Weekday | 45 | ₹4829 | ₹4710 | ₹-119 | -2.5% |
| Jun | 24H Night | Weekend | 10 | ₹9300 | ₹8370 | ₹-930 | -10.0% |
| Jul | 12H Day | Weekday | 34 | ₹2391 | ₹2432 | ₹41 | 1.7% |
| Jul | 12H Night | Weekday | 8 | ₹2150 | ₹1940 | ₹-210 | -9.8% |
| Jul | 12H Night | Weekend | 1 | ₹3000 | ₹960 | ₹-2040 | -68.0% |
| Jul | 24H Night | Weekday | 10 | ₹3372 | ₹3079 | ₹-294 | -8.7% |
| Jul | 24H Night | Weekend | 10 | ₹4900 | ₹4359 | ₹-541 | -11.0% |
| Aug | 12H Day | Weekday | 23 | ₹2113 | ₹1868 | ₹-245 | -11.6% |
| Aug | 12H Night | Weekday | 5 | ₹2000 | ₹1762 | ₹-238 | -11.9% |
| Aug | 24H Day | Weekday | 3 | ₹3500 | ₹3850 | ₹350 | 10.0% |
| Aug | 24H Night | Weekday | 8 | ₹4227 | ₹3685 | ₹-543 | -12.8% |
| Aug | 24H Night | Weekend | 9 | ₹3744 | ₹3481 | ₹-263 | -7.0% |
| Sep | 12H Day | Weekday | 26 | ₹1812 | ₹1858 | ₹47 | 2.6% |
| Sep | 12H Night | Weekday | 8 | ₹2362 | ₹2107 | ₹-256 | -10.8% |
| Sep | 12H Night | Weekend | 3 | ₹2767 | ₹2490 | ₹-277 | -10.0% |
| Sep | 24H Night | Weekday | 1 | ₹7565 | ₹3017 | ₹-4548 | -60.1% |
| Sep | 24H Night | Weekend | 3 | ₹3167 | ₹2808 | ₹-358 | -11.3% |
| Oct | 12H Day | Weekday | 25 | ₹2284 | ₹2680 | ₹396 | 17.3% |
| Oct | 12H Night | Weekday | 5 | ₹2600 | ₹2340 | ₹-260 | -10.0% |
| Oct | 12H Night | Weekend | 1 | ₹2200 | ₹3410 | ₹1210 | 55.0% |
| Oct | 24H Day | Weekday | 3 | ₹3333 | ₹3444 | ₹111 | 3.3% |
| Oct | 24H Night | Weekday | 14 | ₹3796 | ₹3223 | ₹-573 | -15.1% |
| Oct | 24H Night | Weekend | 3 | ₹4000 | ₹3600 | ₹-400 | -10.0% |
| Nov | 12H Day | Weekday | 20 | ₹2130 | ₹2257 | ₹127 | 5.9% |
| Nov | 12H Night | Weekday | 5 | ₹1960 | ₹1740 | ₹-220 | -11.2% |
| Nov | 24H Day | Weekday | 3 | ₹4333 | ₹4693 | ₹359 | 8.3% |
| Nov | 24H Night | Weekday | 11 | ₹3791 | ₹3521 | ₹-270 | -7.1% |
| Nov | 24H Night | Weekend | 8 | ₹4688 | ₹4706 | ₹19 | 0.4% |
| Dec | 12H Day | Weekday | 31 | ₹2071 | ₹2099 | ₹28 | 1.3% |
| Dec | 12H Night | Weekday | 3 | ₹2333 | ₹2267 | ₹-67 | -2.9% |
| Dec | 24H Day | Weekday | 3 | ₹3000 | ₹3764 | ₹764 | 25.5% |
| Dec | 24H Night | Weekday | 10 | ₹3337 | ₹3177 | ₹-161 | -4.8% |
| Dec | 24H Night | Weekend | 7 | ₹4186 | ₹3777 | ₹-409 | -9.8% |