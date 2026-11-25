"""Panel interactivo: costo y retraso de ejecución vs. resultado de cada estrategia.

Uso (desde la raíz del repo, con los precios ya en caché):
    pip install streamlit
    streamlit run app/dashboard.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))   # para importar src/

import pandas as pd
import streamlit as st

from src.data import download_prices
from src.signals import STRATEGIES
from src.backtest import run_backtest
from src.metrics import summarize

st.title("Quant backtest explorer")
px = download_prices(cache=str(ROOT / "data/raw/prices.parquet"))
name = st.selectbox("Estrategia", list(STRATEGIES))
cost = st.slider("Costo por operación (bps)", 0, 50, 5)
delay = st.radio("Retraso de ejecución (días)", [0, 1], index=1, horizontal=True)

start = px.index[260]
res = run_backtest(px, STRATEGIES[name](px), cost, delay, start)
bh = run_backtest(px, STRATEGIES["buy_and_hold"](px), cost, delay, start)

st.line_chart(pd.DataFrame({name: res["equity"], "buy_and_hold": bh["equity"]}))
st.dataframe(pd.DataFrame([summarize(res, name), summarize(bh, "buy_and_hold")])
               .set_index("strategy").round(3))
st.caption("Proyecto educativo. No es asesoría financiera.")
