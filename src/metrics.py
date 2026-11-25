import numpy as np
import pandas as pd

DAYS = 252


def cagr(r: pd.Series) -> float:
    return float((1 + r).prod() ** (DAYS / len(r)) - 1)


def ann_vol(r: pd.Series) -> float:
    return float(r.std() * np.sqrt(DAYS))


def sharpe(r: pd.Series) -> float:
    """Sharpe anualizado con tasa libre de riesgo = 0 (simplificación; declárala)."""
    s = r.std()
    return float(r.mean() / s * np.sqrt(DAYS)) if s > 0 else 0.0


def sortino(r: pd.Series) -> float:
    downside = np.sqrt((np.minimum(r, 0) ** 2).mean())
    return float(r.mean() / downside * np.sqrt(DAYS)) if downside > 0 else 0.0


def max_drawdown(r: pd.Series) -> float:
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def calmar(r: pd.Series) -> float:
    mdd = abs(max_drawdown(r))
    return float(cagr(r) / mdd) if mdd > 0 else 0.0


def summarize(res: pd.DataFrame, name: str = "strategy") -> dict:
    """res = salida de run_backtest."""
    r, years = res["net"], len(res) / DAYS
    return {
        "strategy": name,
        "cagr": cagr(r), "vol": ann_vol(r), "sharpe": sharpe(r), "sortino": sortino(r),
        "max_dd": max_drawdown(r), "calmar": calmar(r),
        "turnover_yr": float(res["turnover"].sum() / years),
        "cost_drag_yr": float(res["cost"].sum() / years),
    }
