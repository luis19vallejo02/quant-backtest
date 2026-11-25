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

## Step 5 sensitivity runs (same fixed parameters; not counted as new strategy trials)
- Cost sensitivity: 0, 5, 10, 25 bps for the 5 strategies (2006-01-13 to 2025-12-30).
- Execution delay sensitivity: delay = 0, 1, 2 days at 5 bps.

## Step 6 walk-forward grids (declared before running; 32 trials in total)
Train 5 years / test 1 year, rolling; parameters chosen by in-sample Sharpe; out-of-sample 2010-2025.

| Strategy | Grid | Combinations |
|---|---|---|
| sma_cross | fast: 20, 50, 100; slow: 100, 150, 200, 250 (fast < slow) | 11 |
| momentum | lookback: 126, 189, 252; skip: 0, 21 | 6 |
| mean_reversion | window: 10, 20, 40; entry_z: -0.5, -1.0, -1.5 | 9 |
| vol_target | target: 0.08, 0.10, 0.15; window: 21, 63 | 6 |

The Step 3 fixed parameters are included in these grids, so they are not extra trials.
**Total trials so far: 32.** No other variants have been tried.
