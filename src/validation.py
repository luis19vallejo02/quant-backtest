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


# ---------------------------------------------------------------------------
# Paso 7: robustez, sobreajuste y significancia estadística
# ---------------------------------------------------------------------------
from scipy import stats

EULER = 0.5772156649


def _ann_sharpe(x):
    return x.mean() / x.std() * np.sqrt(252)


def block_bootstrap_sharpe(r: pd.Series, block=20, n_boot=2000, seed=42):
    """IC 95 % del Sharpe anual. Se remuestrean bloques de 20 días para respetar
    la volatilidad agrupada (un bootstrap día por día sería demasiado optimista)."""
    rng = np.random.default_rng(seed)
    x = r.values
    n = len(x)
    n_blocks = int(np.ceil(n / block))
    out = []
    for _ in range(n_boot):
        starts = rng.integers(0, n - block + 1, n_blocks)
        s = np.concatenate([x[i:i + block] for i in starts])[:n]
        out.append(_ann_sharpe(s))
    return np.percentile(out, [2.5, 97.5])


def paired_bootstrap_diff(a: pd.Series, b: pd.Series, block=20, n_boot=2000, seed=42):
    """Diferencia de Sharpe anual (a - b): IC 95 % y proporción de remuestras con a <= b."""
    rng = np.random.default_rng(seed)
    x = pd.concat([a, b], axis=1).dropna().values
    n = len(x)
    n_blocks = int(np.ceil(n / block))
    diffs = []
    for _ in range(n_boot):
        starts = rng.integers(0, n - block + 1, n_blocks)
        s = np.concatenate([x[i:i + block] for i in starts])[:n]
        diffs.append(_ann_sharpe(s[:, 0]) - _ann_sharpe(s[:, 1]))
    diffs = np.array(diffs)
    return np.percentile(diffs, [2.5, 97.5]), float((diffs <= 0).mean())


def psr(r: pd.Series, sr_benchmark=0.0) -> float:
    """Probabilistic Sharpe Ratio (Sharpe por periodo, no anualizado)."""
    T = len(r)
    sr = r.mean() / r.std()
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    denom = np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return float(stats.norm.cdf((sr - sr_benchmark) * np.sqrt(T - 1) / denom))


def expected_max_sharpe(n_trials: int, var_sr: float) -> float:
    """Sharpe máximo esperado solo por azar entre n_trials intentos sin ventaja real."""
    return float(np.sqrt(var_sr) * ((1 - EULER) * stats.norm.ppf(1 - 1 / n_trials)
                                    + EULER * stats.norm.ppf(1 - 1 / (n_trials * np.e))))


def deflated_sharpe(r: pd.Series, n_trials: int, var_sr: float) -> float:
    """Probabilidad de que el Sharpe supere lo que se esperaría del mejor de n_trials al azar."""
    return psr(r, expected_max_sharpe(n_trials, var_sr))


def timing_placebo(prices, signal, n=500, cost_bps=5.0, start=None, seed=42):
    """Desplaza la señal en el tiempo en bloques circulares: conserva exposición y rotación,
    pero destruye su relación con los retornos. Devuelve (Sharpe real, simulados, p-valor)."""
    rng = np.random.default_rng(seed)
    real = sharpe(run_backtest(prices, signal, cost_bps, start=start)["net"])
    sims = []
    for _ in range(n):
        k = int(rng.integers(252, len(signal) - 252))
        shifted = pd.DataFrame(np.roll(signal.values, k, axis=0),
                               index=signal.index, columns=signal.columns)
        sims.append(sharpe(run_backtest(prices, shifted, cost_bps, start=start)["net"]))
    sims = np.array(sims)
    return real, sims, float((sims >= real).mean())
