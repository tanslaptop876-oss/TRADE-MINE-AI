import pandas as pd
import streamlit as st

from app.main import observability_dashboard
from app.services.decision import DecisionEngine
from app.services.indicators import add_indicators
from app.services.risk import RiskEngine
from dashboard.observability import filter_options, filter_validation_runs, issue_frequency


st.set_page_config(page_title="TradeMind AI", layout="wide")
st.title("TradeMind AI")
st.caption("Trading decision support and read-only paper observability.")

view = st.sidebar.radio(
    "View",
    ("Decision support", "Paper observability"),
)


if view == "Paper observability":
    payload = observability_dashboard()
    summary = payload["paper_validation"]
    safety = payload["safety"]
    runs = summary["recent_runs"]

    st.subheader("Paper validation observability")
    if safety["real_broker_dispatch_enabled"]:
        st.error("Safety lock violated: real broker dispatch is enabled.")
    else:
        st.success("Safety lock active — real broker dispatch is disabled.")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    outcome = filter_col1.selectbox("Outcome", ("all", "valid", "invalid"))
    symbol = filter_col2.selectbox("Symbol", filter_options(runs, "symbol"))
    service_version = filter_col3.selectbox(
        "Service version",
        filter_options(runs, "service_version"),
    )
    filtered_runs = filter_validation_runs(
        runs,
        outcome=outcome,
        symbol=symbol,
        service_version=service_version,
    )

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Health", summary["health_status"].replace("_", " ").title())
    metric_col2.metric("Total runs", summary["total_runs"])
    metric_col3.metric("Valid rate", f'{summary["valid_rate"]:.1%}')
    metric_col4.metric("Filtered runs", len(filtered_runs))

    persistence = summary["history_persistence"]
    st.caption(
        f'History persistence: {persistence["status"]} · '
        f'Gateway mode: {safety["broker_gateway_mode"]}'
    )

    if payload["alerts"]:
        st.subheader("Active alerts")
        for alert in payload["alerts"]:
            st.warning(f'{alert["code"]}: {alert["message"]}')
    else:
        st.info("No active paper-validation alerts.")

    if filtered_runs:
        run_frame = pd.DataFrame(filtered_runs)
        run_frame["valid_numeric"] = run_frame["valid"].astype(int)
        st.subheader("Recent validation runs")
        st.line_chart(run_frame.set_index("run_number")[["valid_numeric"]])
        st.dataframe(run_frame.drop(columns=["valid_numeric"]), use_container_width=True)

        frequencies = issue_frequency(filtered_runs)
        if frequencies:
            st.subheader("Issue frequency")
            issue_frame = pd.DataFrame(frequencies).set_index("issue")
            st.bar_chart(issue_frame)
    else:
        st.info("No validation runs match the selected filters.")

else:
    uploaded = st.file_uploader("Upload OHLCV CSV", type=["csv"])
    capital = st.number_input(
        "Capital",
        min_value=1000.0,
        value=100000.0,
        step=1000.0,
    )

    if uploaded:
        df = pd.read_csv(uploaded)
        df = add_indicators(df.to_dict("records"))
        if len(df) >= 55:
            decision = DecisionEngine().evaluate(df)
            risk = RiskEngine().size_position(
                capital,
                decision.entry,
                decision.stop_loss,
            )
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
