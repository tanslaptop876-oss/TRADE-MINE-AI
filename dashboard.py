import os

import streamlit as st

from app.services.assets import default_india_registry
from app.services.instruments import upstox_instrument_key
from app.services.market_data import MarketDataRequest, MarketDataService
from app.services.paper_trading import PaperAccount, PaperBroker
from app.services.pipeline import TradingPipeline
from app.services.providers import YFinanceProvider


st.set_page_config(page_title="TradeMind AI", layout="wide")
st.title("TradeMind AI v1.1")
st.caption("Research + live-data-compatible paper trading. Real-money execution is disabled.")

live_token_configured = bool(os.getenv("UPSTOX_ACCESS_TOKEN"))
status1, status2, status3 = st.columns(3)
status1.metric("Market data mode", "LIVE READY" if live_token_configured else "HISTORICAL")
status2.metric("Execution mode", "PAPER")
status3.metric("Real-money orders", "DISABLED")

if live_token_configured:
    st.success("Upstox live-data credentials detected. Live quotes can be validated before paper execution.")
else:
    st.info("Set UPSTOX_ACCESS_TOKEN in the environment to enable live-data connectivity. No token is stored in code.")

registry = default_india_registry()
symbols = [asset.symbol for asset in registry.list()]

symbol = st.selectbox("Symbol", symbols, index=0)
interval = st.selectbox("Interval", ["1d", "1h"], index=0)
capital = st.number_input("Paper capital", min_value=1000.0, value=100000.0, step=1000.0)
risk_per_trade = st.slider("Risk per trade", 0.1, 5.0, 1.0, 0.1) / 100

if symbol in {"RELIANCE", "TCS"}:
    st.caption(f"Upstox instrument: {upstox_instrument_key(symbol)}")

if st.button("Run historical paper signal", type="primary"):
    provider = YFinanceProvider()
    service = MarketDataService(provider)
    request = MarketDataRequest(symbol=f"{symbol}.NS" if symbol in {"RELIANCE", "TCS"} else symbol, interval=interval)
    candles = service.get_candles(request)

    if len(candles) < 55:
        st.error("Not enough historical candles returned for the selected instrument/interval.")
    else:
        account = PaperAccount(starting_cash=capital)
        broker = PaperBroker(account, registry)
        pipeline = TradingPipeline(broker=broker, registry=registry, risk_per_trade=risk_per_trade)
        result = pipeline.run(symbol=symbol, candles=candles.to_dict("records"))

        decision = result["decision"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Action", decision["action"])
        c2.metric("Confidence", f"{decision['confidence']:.1f}%")
        c3.metric("Entry", f"{decision['entry']:.2f}")
        c4.metric("Risk/Reward", f"{decision['risk_reward']:.2f}")

        st.subheader("Price history")
        st.line_chart(candles.set_index("timestamp")["close"])

        st.subheader("Decision evidence")
        for item in decision["evidence"]:
            st.write(f"- {item}")

        st.subheader("Risk and paper execution")
        st.json({"risk": result["risk"], "execution": result["execution"]})

        st.subheader("Paper account")
        st.json({
            "cash": round(account.cash, 2),
            "positions": account.positions,
            "trades": account.trades,
        })
