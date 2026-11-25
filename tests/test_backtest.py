import numpy as np
import pandas as pd
import pytest

from src.backtest import run_backtest
from src.metrics import max_drawdown
from src.signals import STRATEGIES
from src.validation import (GRIDS, param_combos, walk_forward, expected_max_sharpe,
                            block_bootstrap_sharpe, psr)


def _prices(n=600, seed=0, start="2010-01-01"):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=n)
    rets = rng.normal(0.0004, 0.01, size=(n, 2))
    return pd.DataFrame(100 * np.cumprod(1 + rets, axis=0), index=idx, columns=["A", "B"])


@pytest.mark.parametrize("name", list(STRATEGIES))
def test_signals_have_no_lookahead(name):
    px = _prices()
    full = STRATEGIES[name](px)
    trunc = STRATEGIES[name](px.iloc[:400])
    pd.testing.assert_frame_equal(full.iloc[:400], trunc)


def test_signal_is_executed_after_the_delay():
    px = _prices()
    sig = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    sig.iloc[100] = 1.0                                   # señal solo el día 100
    res = run_backtest(px, sig, cost_bps=0, delay=1)
    r = px.pct_change()
    assert res["gross"].iloc[:102].abs().sum() == 0       # nada antes del día 102
    assert res["gross"].iloc[102] == pytest.approx(r.iloc[102].mean())
    assert res["gross"].iloc[103:].abs().sum() == 0


def test_costs_equal_turnover_times_bps():
    px = _prices()
    sig = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    sig.iloc[100] = 1.0
    res = run_backtest(px, sig, cost_bps=10, delay=1)
    assert res["cost"].iloc[102] == pytest.approx(10 / 1e4)    # entra con 100 % del capital
    assert res["cost"].sum() == pytest.approx(2 * 10 / 1e4)    # entra y sale
    assert (res["net"] <= res["gross"] + 1e-12).all()


def test_max_drawdown_simple_case():
    r = pd.Series([0.10, -0.50, 0.20])                    # 1.10 -> 0.55 -> 0.66
    assert max_drawdown(r) == pytest.approx(-0.5)


def test_param_combos_excludes_invalid_pairs():
    combos = list(param_combos(GRIDS["sma_cross"]))
    assert len(combos) == 11 and all(p["fast"] < p["slow"] for p in combos)


def test_more_trials_raise_the_bar():
    assert expected_max_sharpe(100, 1e-4) > expected_max_sharpe(10, 1e-4)
    r = pd.Series(np.random.default_rng(0).normal(0.0004, 0.01, 1000))
    assert 0.0 <= psr(r) <= 1.0


def test_bootstrap_is_reproducible():
    r = pd.Series(np.random.default_rng(0).normal(0.0004, 0.01, 500))
    assert np.allclose(block_bootstrap_sharpe(r, n_boot=200), block_bootstrap_sharpe(r, n_boot=200))


def test_walk_forward_ignores_the_future():
    """Cambiar los precios de 2011 en adelante no debe alterar la ventana de prueba de 2008."""
    px = _prices(n=2400, start="2005-01-03")              # ~2005 a 2014
    grid = {"fast": [20, 50], "slow": [100, 150]}
    kw = dict(train_years=3, test_years=1, warmup=150)
    a, _ = walk_forward(px, STRATEGIES["sma_cross"], grid, **kw)

    px2 = px.copy()
    tail = px2.index >= "2011-01-01"
    noise = np.random.default_rng(1).uniform(0.5, 1.5, size=(tail.sum(), 2))
    px2.loc[tail] = px2.loc[tail].values * noise
    b, _ = walk_forward(px2, STRATEGIES["sma_cross"], grid, **kw)

    pd.testing.assert_series_equal(a.loc["2008", "net"], b.loc["2008", "net"])
