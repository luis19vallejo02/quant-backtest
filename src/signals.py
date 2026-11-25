import numpy as np
import pandas as pd


def buy_and_hold(prices: pd.DataFrame) -> pd.DataFrame:
    """Benchmark: siempre invertido."""
    return pd.DataFrame(1.0, index=prices.index, columns=prices.columns)


def sma_cross(prices, fast=50, slow=200):
    """Tendencia: 1 si la media rápida está sobre la lenta, 0 si no."""
    return (prices.rolling(fast).mean() > prices.rolling(slow).mean()).astype(float)


def momentum(prices, lookback=252, skip=21):
    """Momentum 12-1: 1 si el retorno de los últimos 12 meses (sin el último) es positivo."""
    past = prices.shift(skip) / prices.shift(lookback) - 1
    return (past > 0).astype(float)


def mean_reversion(prices, window=20, entry_z=-1.0):
    """Reversión: 1 cuando el precio cae más de 1 desv. est. bajo su media móvil."""
    z = (prices - prices.rolling(window).mean()) / prices.rolling(window).std()
    return (z < entry_z).astype(float)


def vol_target(prices, target=0.10, window=21, max_leverage=1.0):
    """Siempre invertido; el tamaño baja cuando la volatilidad reciente sube. Sin apalancamiento."""
    vol = prices.pct_change().rolling(window).std() * np.sqrt(252)
    return (target / vol).clip(upper=max_leverage)


STRATEGIES = {
    "buy_and_hold": buy_and_hold,
    "sma_cross": sma_cross,
    "momentum": momentum,
    "mean_reversion": mean_reversion,
    "vol_target": vol_target,
}


def monthly(signal_fn):
    """Envuelve una estrategia para que cambie de posición solo al cierre de cada mes.

    La señal del último día del calendario (no del último día hábil) se mantiene hasta el
    mes siguiente: si el mes termina en día hábil, el cambio se registra ese día; si termina
    en fin de semana, el primer día hábil del mes siguiente. Nunca cambia a mitad de mes.
    """
    def wrapped(prices, **kw):
        sig = signal_fn(prices, **kw)
        month_end = sig.resample("ME").last()                  # valor al último día de cada mes
        return month_end.reindex(sig.index, method="ffill")    # se mantiene hasta el mes siguiente
    return wrapped
