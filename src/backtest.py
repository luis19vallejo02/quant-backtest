import pandas as pd


def run_backtest(prices: pd.DataFrame, signal: pd.DataFrame, cost_bps: float = 5.0,
                 delay: int = 1, start=None) -> pd.DataFrame:
    """Backtest vectorizado de una cartera de pesos iguales entre activos.

    signal: posición deseada por activo, entre 0 y 1, calculada con el cierre de t.
    delay:  días de retraso entre calcular la señal y operar (1 = cierre siguiente).
    """
    rets = prices.pct_change()
    n = prices.shape[1]
    target = signal.reindex(prices.index).fillna(0.0) / n      # peso de cada activo; el resto es efectivo
    weights = target.shift(1 + delay).fillna(0.0)               # posición que gana el retorno de cada día

    gross = (weights * rets.fillna(0.0)).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)     # fracción del capital operada
    cost = turnover * cost_bps / 1e4
    out = pd.DataFrame({"gross": gross, "cost": cost, "net": gross - cost, "turnover": turnover})
    if start is not None:
        out = out.loc[start:]
    out["equity"] = (1 + out["net"]).cumprod()
    return out
