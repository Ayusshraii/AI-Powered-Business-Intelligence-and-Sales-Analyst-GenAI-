import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from src import queries, agent
from src.anomaly import flag_anomalies
from src.db import DB_PATH

st.set_page_config(page_title="Sales Analyst Agent", layout="wide")
st.title("Sales Analyst Agent")

if not DB_PATH.exists():
    st.error("Database not found. Run: python -m src.db data/superstore.csv")
    st.stop()

monthly = queries.monthly_summary()
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Ask your data", "Profit investigation", "Action tracker"])

with tab1:
    last = monthly.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue (latest month)", f"{last.revenue:,.0f}", f"{last.revenue_mom_pct}% MoM")
    c2.metric("Profit (latest month)", f"{last.profit:,.0f}", f"{last.profit_mom_pct}% MoM")
    c3.metric("Margin", f"{last.margin_pct}%")
    c4.metric("Avg discount", f"{last.avg_discount_pct}%")
    st.plotly_chart(px.line(monthly, x="month", y=["revenue", "profit"], title="Revenue and profit by month"),
                    use_container_width=True)
    st.subheader("Anomalies")
    st.dataframe(flag_anomalies(monthly), use_container_width=True)
    st.subheader("Risky products (high sales, low or negative margin)")
    st.dataframe(queries.risky_products(), use_container_width=True)
    st.subheader("Margin by sub-category")
    st.dataframe(queries.category_margins(), use_container_width=True)

with tab2:
    q = st.text_input("Ask a question", "Which five products generated the most revenue?")
    if st.button("Ask") and q:
        with st.spinner("Thinking..."):
            res = agent.ask_data(q)
        if res["error"]:
            st.error(f"Could not get a valid query: {res['error']}")
        else:
            st.code(res["sql"], language="sql")
            st.dataframe(res["table"], use_container_width=True)
            st.write(agent.explain(q, res["table"]))

with tab3:
    month = st.selectbox("Month to investigate", monthly["month"].tolist()[1:], index=len(monthly) - 2)
    if st.button("Why did profit change?"):
        with st.spinner("Running queries..."):
            changes, bands, text = agent.investigate_profit(month)
        st.subheader("Evidence")
        st.dataframe(changes, use_container_width=True)
        st.dataframe(bands, use_container_width=True)
        st.subheader("Explanation")
        st.write(text)

with tab4:
    # tracker lives in its own db so the sales db stays read-only
    tcon = sqlite3.connect(DB_PATH.parent / "tracker.db")
    tcon.execute("""CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY, created TEXT,
                    recommendation TEXT, kpi TEXT, baseline REAL, status TEXT, outcome TEXT)""")
    with st.form("new_action", clear_on_submit=True):
        rec = st.text_input("Recommendation")
        kpi = st.text_input("KPI to measure (e.g. Furniture margin %)")
        base = st.number_input("Baseline value", value=0.0)
        if st.form_submit_button("Add") and rec:
            tcon.execute("INSERT INTO actions (created, recommendation, kpi, baseline, status, outcome) VALUES (date('now'),?,?,?,'open','')",
                         (rec, kpi, base))
            tcon.commit()
    st.dataframe(pd.read_sql_query("SELECT * FROM actions", tcon), use_container_width=True)
    tcon.close()
