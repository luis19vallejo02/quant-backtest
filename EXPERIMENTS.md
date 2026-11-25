# Experiment log

Every strategy variant or parameter set evaluated in this project, including discarded ones.
This count feeds the number of trials used in the Deflated Sharpe Ratio (Step 7).

| Date | Step | Strategy | Parameters | Notes |
|---|---|---|---|---|
| 2026-11-25 | 3 | buy_and_hold | — | Benchmark, equal weight 1/5 per ETF |
| 2026-11-25 | 3 | sma_cross | fast=50, slow=200 | Fixed from literature, not optimized |
| 2026-11-25 | 3 | momentum | lookback=252, skip=21 | Fixed from literature, not optimized |
| 2026-11-25 | 3 | mean_reversion | window=20, entry_z=-1.0 | Fixed from literature, not optimized |
| 2026-11-25 | 3 | vol_target | target=0.10, window=21, max_leverage=1.0 | Fixed from literature, not optimized |

Trials so far: 4 strategies with fixed parameters (plus the benchmark). No results seen yet.
