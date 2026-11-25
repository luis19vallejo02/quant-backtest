import itertools
import numpy as np
import pandas as pd

from src.backtest import run_backtest
from src.metrics import sharpe

GRIDS = {
    "sma_cross": {"fast": [20, 50, 100], "slow": [100, 150, 200, 250]},
    "momentum": {"lookback": [126, 189, 252], "skip": [0, 21]},
    "mean_reversion": {"window": [10, 20, 40], "entry_z": [-0.5, -1.0, -1.5]},
    "vol_target": {"target": [0.08, 0.10, 0.15], "window": [21, 63]},
}


def param_combos(grid: dict):
    keys = list(grid)
    for vals in itertools.product(*grid.values()):
        p = dict(zip(keys, vals))
        if "fast" in p and p["fast"] >= p["slow"]:
            continue
        yield p


def walk_forward(prices, signal_fn, grid, train_years=5, test_years=1,
                 cost_bps=5.0, warmup=260):
    """Elige parámetros con el entrenamiento y los aplica a la ventana siguiente.

    Devuelve (retornos fuera de muestra concatenados, parámetros elegidos por año).
    """
    years = sorted(set(prices.index.year))
    first_valid = prices.index[warmup]
    parts, chosen = [], []

    for i in range(train_years, len(years) - test_years + 1, test_years):
        tr_start = max(prices.index[prices.index.year >= years[i - train_years]][0], first_valid)
        te_start = prices.index[prices.index.year >= years[i]][0]
        te_end = prices.index[prices.index.year < years[i] + test_years][-1]
        tr_end = prices.index[prices.index < te_start][-1]

        # 1) Elegir parámetros SOLO con datos hasta el fin del entrenamiento
        best_p, best_s = None, -np.inf
        px_tr = prices.loc[:tr_end]
        for p in param_combos(grid):
            res = run_backtest(px_tr, signal_fn(px_tr, **p), cost_bps, start=tr_start)
            s = sharpe(res["net"])
            if s > best_s:
                best_p, best_s = p, s

        # 2) Aplicarlos al periodo de prueba (la señal solo usa información pasada)
        px_te = prices.loc[:te_end]
        res = run_backtest(px_te, signal_fn(px_te, **best_p), cost_bps, start=te_start)
        parts.append(res[["gross", "cost", "net", "turnover"]])
        chosen.append({"test_year": years[i], **best_p, "train_sharpe": best_s})

    return pd.concat(parts), pd.DataFrame(chosen).set_index("test_year")
