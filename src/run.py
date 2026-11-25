import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from src.data import download_prices
from src.signals import STRATEGIES
from src.backtest import run_backtest
from src.metrics import summarize
from src.validation import (GRIDS, param_combos, walk_forward, block_bootstrap_sharpe,
                            paired_bootstrap_diff, deflated_sharpe)


def main(config_path: str = "config.yaml"):
    cfg = yaml.safe_load(open(config_path))
    d, b, w, v = cfg["data"], cfg["backtest"], cfg["walk_forward"], cfg["validation"]

    px = download_prices(d["tickers"], d["start"], d["end"], d["cache"])
    start = px.index[b["warmup_days"]]

    # 1) Parámetros fijos, periodo completo
    full = {n: summarize(run_backtest(px, fn(px), b["cost_bps"], start=start), n)
            for n, fn in STRATEGIES.items()}

    # 2) Walk-forward fuera de muestra
    oos = {n: walk_forward(px, STRATEGIES[n], g, w["train_years"], w["test_years"],
                           b["cost_bps"], b["warmup_days"])[0] for n, g in GRIDS.items()}
    oos_start = oos["sma_cross"].index[0]
    bench = run_backtest(px, STRATEGIES["buy_and_hold"](px), b["cost_bps"], start=oos_start)

    # 3) Intentos totales, para el Deflated Sharpe Ratio
    trial_sr = []
    for n, g in GRIDS.items():
        for p in param_combos(g):
            r = run_backtest(px, STRATEGIES[n](px, **p), b["cost_bps"], start=oos_start)["net"]
            trial_sr.append(r.mean() / r.std())
    n_trials, var_sr = len(trial_sr), float(np.var(trial_sr, ddof=1))

    # 4) Estadística fuera de muestra
    wf = {}
    for n, res in oos.items():
        lo, hi = block_bootstrap_sharpe(res["net"], v["block"], v["n_boot"], v["seed"])
        (dlo, dhi), p = paired_bootstrap_diff(res["net"], bench["net"], v["block"],
                                              v["n_boot"], v["seed"])
        wf[n] = {**summarize(res, n), "sharpe_ci95": [float(lo), float(hi)],
                 "diff_vs_buy_hold_ci95": [float(dlo), float(dhi)], "p_not_better": p,
                 "dsr": deflated_sharpe(res["net"], n_trials, var_sr)}

    out = {
        "data_sha256": hashlib.sha256(Path(d["cache"]).read_bytes()).hexdigest()[:12],
        "oos_period": [str(oos_start.date()), str(px.index[-1].date())],
        "n_trials": n_trials,
        "buy_and_hold_oos": summarize(bench, "buy_and_hold"),
        "walk_forward_oos": wf,
        "full_sample_fixed_params": full,
    }
    path = Path(cfg["outputs"]["metrics_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(path, "w"), indent=2, default=str)
    print(json.dumps(out["walk_forward_oos"], indent=2, default=str))


if __name__ == "__main__":
    main()
