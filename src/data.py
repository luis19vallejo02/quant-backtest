from pathlib import Path
import pandas as pd
import yfinance as yf

TICKERS = ["SPY", "QQQ", "TLT", "GLD", "EEM"]


def download_prices(tickers=TICKERS, start="2005-01-01", end="2025-12-31",
                    cache="data/raw/prices.parquet", refresh=False) -> pd.DataFrame:
    """Precios de cierre ajustados. Usa caché local para no depender de la red."""
    path = Path(cache)
    if path.exists() and not refresh:
        return pd.read_parquet(path)
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"].copy()
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    prices = prices[tickers].sort_index()
    path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(path)
    return prices


def to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Retornos simples diarios."""
    return prices.pct_change().dropna(how="all")
