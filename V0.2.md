import streamlit as st
import pandas as pd
from app.services.indicators import add_indicators
from app.services.decision import DecisionEngine
from app.services.risk import RiskEngine

st.set_page_config(page_title="TradeMind AI", layout="wide")
st.title("TradeMind AI")
st.caption("Trading decision-support MVP — validate before live trading.")

uploaded = st.file_uploader("Upload OHLCV CSV", type=["csv"])
capital = st.number_input("Capital", min_value=1000.0, value=100000.0, step=1000.0)

if uploaded:
    df = pd.read_csv(uploaded)
    df = add_indicators(df.to_dict("records"))
    if len(df) >= 55:
        decision = DecisionEngine().evaluate(df)
        risk = RiskEngine().size_position(capital, decision.entry, decision.stop_loss)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Action", decision.action)
        c2.metric("Confidence", f"{decision.confidence:.0f}%")
        c3.metric("Entry", f"{decision.entry:.2f}")
        c4.metric("R:R", f"{decision.risk_reward:.2f}")
        st.subheader("Evidence")
        for item in decision.evidence:
            st.write("•", item)
        st.subheader("Risk")
        st.json(risk)
        st.subheader("Latest indicators")
        st.dataframe(df.tail(20), use_container_width=True)
    else:
        st.warning("Upload at least 55 candles.")
