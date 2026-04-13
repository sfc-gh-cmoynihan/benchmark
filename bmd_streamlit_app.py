import streamlit as st
import altair as alt
import pandas as pd
import json
from snowflake.snowpark.context import get_active_session

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

st.set_page_config(
    page_title="Benchmark Minerals - Pricing Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

session = get_active_session()

SAMPLE_QUESTIONS = [
    "What is the latest copper price?",
    "Compare lithium and cobalt prices over the last 6 months",
    "Which metal had the biggest price increase this year?",
    "What are the top 5 most expensive metals right now?",
    "Show me the price trend for platinum on LBMA",
    "How has the price of nickel changed month over month?",
    "What exchanges track palladium pricing?",
    "What is the average copper price by region?",
    "Which materials have the most price volatility?",
    "What rare earths pricing data is available?",
    "What is the copper price trend over the last 3 months?",
    "How does copper compare to lithium in price performance?",
    "What is the supply risk rating for copper?",
    "What are analysts predicting for copper prices this year?",
    "What are the key risks for battery minerals supply chains?",
]

TABLE = "BENCHMARKMINERALS_DB.PUBLIC.BATTERY_CRITICAL_MINERALS_PRICING_IT"

def call_agent(question, messages_history):
    history_json = json.dumps(messages_history) if messages_history else "[]"
    result = session.call("BENCHMARKMINERALS_DB.PUBLIC.CALL_ASK_BENCHMARK_AGENT", question, history_json)
    return result if result else "No response from agent."

if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []
if "show_agent" not in st.session_state:
    st.session_state.show_agent = False

st.markdown(
    """<style>
    div[data-testid="stHorizontalBlock"] {
        align-items: flex-end;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child div[data-testid="stButton"] {
        margin-top: 24px;
    }
    div.floating-chat-container button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 8px 20px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4) !important;
    }
    div.floating-chat-container button:hover {
        box-shadow: 0 6px 20px rgba(102,126,234,0.6) !important;
    }
    </style>""",
    unsafe_allow_html=True,
)

st.image("https://www.benchmarkminerals.com/assets/logos/logo-black.svg", width=280)

if st.session_state.show_agent:
    with st.sidebar:
        st.subheader("Lets Chat")
        if st.button("Clear Chat", key="clear_agent"):
            st.session_state.agent_messages = []
            safe_rerun()
        for msg in st.session_state.agent_messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="background:#e3f2fd;padding:10px 14px;border-radius:12px;margin:6px 0 2px 20px;text-align:right;"><b>You</b><br/>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#f5f5f5;padding:10px 14px;border-radius:12px;margin:2px 20px 6px 0;"><b>Benchmark</b><br/>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
        if not st.session_state.agent_messages:
            st.caption("Try asking:")
            for sq in SAMPLE_QUESTIONS[:5]:
                if st.button(sq, key=f"sq_{sq}", use_container_width=True):
                    st.session_state.agent_messages.append({"role": "user", "content": sq})
                    with st.spinner("Thinking..."):
                        answer = call_agent(sq, [])
                    st.session_state.agent_messages.append({"role": "assistant", "content": answer})
                    safe_rerun()
        with st.form("agent_form", clear_on_submit=True):
            prompt = st.text_input("Ask about minerals, pricing, indices...", key="agent_input")
            submitted = st.form_submit_button("Send")
            if submitted and prompt:
                st.session_state.agent_messages.append({"role": "user", "content": prompt})
                with st.spinner("Thinking..."):
                    answer = call_agent(prompt, st.session_state.agent_messages[:-1])
                st.session_state.agent_messages.append({"role": "assistant", "content": answer})
                safe_rerun()

st.title("Precious Metals & Critical Minerals Daily Pricing")

@st.cache_data(ttl=3600)
def load_filter_options():
    result = session.sql(f"""
        SELECT
            MIN(ASSESSMENT_DATE) AS MIN_DATE,
            MAX(ASSESSMENT_DATE) AS MAX_DATE,
            ARRAY_AGG(DISTINCT MATERIAL) WITHIN GROUP (ORDER BY MATERIAL) AS MATERIALS,
            ARRAY_AGG(DISTINCT EXCHANGE) WITHIN GROUP (ORDER BY EXCHANGE) AS EXCHANGES
        FROM {TABLE}
        WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL
    """).to_pandas()
    materials = json.loads(result["MATERIALS"].iloc[0])
    exchanges = json.loads(result["EXCHANGES"].iloc[0])
    return result["MIN_DATE"].iloc[0], result["MAX_DATE"].iloc[0], materials, exchanges

min_date_val, max_date_val, all_metals, all_exchanges = load_filter_options()
min_date = pd.Timestamp(min_date_val).date()
max_date = pd.Timestamp(max_date_val).date()

date_col1, date_col2, metal_col, exchange_col, chat_col = st.columns([1, 1, 0.88, 0.88, 1.5])

with date_col1:
    date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with date_col2:
    date_to = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
with metal_col:
    selected_metal = st.selectbox("Material", ["All"] + all_metals)
with exchange_col:
    selected_exchange = st.selectbox("Exchange", ["All"] + all_exchanges)
with chat_col:
    st.markdown('<div class="floating-chat-container">', unsafe_allow_html=True)
    if st.button("\U0001f4ac Let's Chat", key="toggle_agent"):
        st.session_state.show_agent = not st.session_state.show_agent
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

selected_metals = all_metals if selected_metal == "All" else [selected_metal]
selected_exchanges = all_exchanges if selected_exchange == "All" else [selected_exchange]


@st.cache_data(ttl=600)
def load_filtered_data(_date_from, _date_to, _metals, _exchanges):
    metal_list = ",".join([f"'{m}'" for m in _metals])
    exchange_list = ",".join([f"'{e}'" for e in _exchanges])
    df = session.sql(f"""
        SELECT ASSESSMENT_DATE, MATERIAL, EXCHANGE,
               PRICE_OPEN_USD_PER_OZ, PRICE_CLOSE_USD_PER_OZ,
               PRICE_HIGH_USD_PER_OZ, PRICE_LOW_USD_PER_OZ
        FROM {TABLE}
        WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL
          AND ASSESSMENT_DATE BETWEEN '{_date_from}' AND '{_date_to}'
          AND MATERIAL IN ({metal_list})
          AND EXCHANGE IN ({exchange_list})
        ORDER BY ASSESSMENT_DATE
    """).to_pandas()
    df["ASSESSMENT_DATE"] = pd.to_datetime(df["ASSESSMENT_DATE"])
    return df

@st.cache_data(ttl=600)
def load_daily_changes(_date_from, _date_to):
    return session.sql(f"""
        WITH ranked AS (
            SELECT MATERIAL, ASSESSMENT_DATE, AVG(PRICE_CLOSE_USD_PER_OZ) AS AVG_CLOSE,
                   ROW_NUMBER() OVER (PARTITION BY MATERIAL ORDER BY ASSESSMENT_DATE DESC) AS rn
            FROM {TABLE}
            WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL
              AND ASSESSMENT_DATE BETWEEN '{_date_from}' AND '{_date_to}'
            GROUP BY MATERIAL, ASSESSMENT_DATE
        )
        SELECT
            c.MATERIAL AS "Material",
            ROUND(c.AVG_CLOSE - p.AVG_CLOSE, 2) AS "Daily Change",
            ROUND((c.AVG_CLOSE - p.AVG_CLOSE) / NULLIF(p.AVG_CLOSE, 0) * 100, 2) AS "Change %"
        FROM ranked c
        JOIN ranked p ON c.MATERIAL = p.MATERIAL AND c.rn = 1 AND p.rn = 2
        ORDER BY c.MATERIAL
    """).to_pandas()

@st.cache_data(ttl=600)
def generate_csv():
    all_raw = session.sql(f"""
        SELECT ASSESSMENT_DATE AS "Date", MATERIAL AS "Metal", EXCHANGE AS "Exchange",
               PRICE_OPEN_USD_PER_OZ AS "Open", PRICE_CLOSE_USD_PER_OZ AS "Close",
               PRICE_HIGH_USD_PER_OZ AS "High", PRICE_LOW_USD_PER_OZ AS "Low"
        FROM {TABLE}
        WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL
        ORDER BY ASSESSMENT_DATE
    """).to_pandas()
    return all_raw.to_csv(index=False).encode("utf-8")

filtered = load_filtered_data(str(date_from), str(date_to), tuple(selected_metals), tuple(selected_exchanges))

if filtered.empty:
    st.warning("No data matches the selected filters.")
else:
    st.subheader("Close Price (USD/oz)")
    chart = (
        alt.Chart(filtered)
        .mark_line()
        .encode(
            x=alt.X("ASSESSMENT_DATE:T", title="Date"),
            y=alt.Y("PRICE_CLOSE_USD_PER_OZ:Q", title="Close Price (USD/oz)"),
            color=alt.Color("MATERIAL:N", title="Metal"),
            strokeDash=alt.StrokeDash("EXCHANGE:N", title="Exchange"),
            tooltip=[
                alt.Tooltip("ASSESSMENT_DATE:T", title="Date"),
                alt.Tooltip("MATERIAL:N", title="Metal"),
                alt.Tooltip("EXCHANGE:N", title="Exchange"),
                alt.Tooltip("PRICE_OPEN_USD_PER_OZ:Q", title="Open", format=",.2f"),
                alt.Tooltip("PRICE_CLOSE_USD_PER_OZ:Q", title="Close", format=",.2f"),
                alt.Tooltip("PRICE_HIGH_USD_PER_OZ:Q", title="High", format=",.2f"),
                alt.Tooltip("PRICE_LOW_USD_PER_OZ:Q", title="Low", format=",.2f"),
            ],
        )
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Daily Change Heatmap")

    summary = load_daily_changes(str(date_from), str(date_to))

    n_materials = len(summary)
    rows = (n_materials + 3) // 4
    mat_list = summary.to_dict("records")

    for r in range(rows):
        box_cols = st.columns(4)
        for c in range(4):
            idx = r * 4 + c
            if idx < n_materials:
                item = mat_list[idx]
                with box_cols[c]:
                    change_val = item["Daily Change"] if item["Daily Change"] is not None else 0
                    pct_val = item["Change %"] if item["Change %"] is not None else 0
                    if change_val > 0.01:
                        bg = "#c8e6c9"
                        fg = "#1b5e20"
                        arrow = "&#9650;"
                    elif change_val < -0.01:
                        bg = "#ffcdd2"
                        fg = "#b71c1c"
                        arrow = "&#9660;"
                    else:
                        bg = "#ffe0b2"
                        fg = "#e65100"
                        arrow = "&#9644;"
                    st.markdown(
                        f"""<div style="background-color:{bg};color:{fg};padding:12px 16px;
                        border-radius:8px;margin-bottom:8px;text-align:center;">
                        <div style="font-weight:600;font-size:14px;">{item['Material']}</div>
                        <div style="font-size:20px;font-weight:700;margin:4px 0;">
                        {arrow} {change_val:+.2f}</div>
                        <div style="font-size:13px;">{pct_val:+.2f}%</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    st.caption("Green = Up | Red = Down | Orange = No Change")

    n_cols = min(len(selected_metals), 4)
    if n_cols > 0:
        cols = st.columns(n_cols)
        for i, metal in enumerate(selected_metals):
            with cols[i % n_cols]:
                metal_data = filtered[filtered["MATERIAL"] == metal]
                if not metal_data.empty:
                    latest = metal_data.loc[metal_data["ASSESSMENT_DATE"].idxmax()]
                    first = metal_data.loc[metal_data["ASSESSMENT_DATE"].idxmin()]
                    change = ((latest["PRICE_CLOSE_USD_PER_OZ"] - first["PRICE_CLOSE_USD_PER_OZ"])
                              / first["PRICE_CLOSE_USD_PER_OZ"] * 100)
                    st.metric(
                        metal,
                        f"${latest['PRICE_CLOSE_USD_PER_OZ']:,.2f}",
                        f"{change:+.1f}%",
                    )

    with st.expander("View Raw Data"):
        raw_df = filtered.rename(columns={
            "ASSESSMENT_DATE": "Date", "MATERIAL": "Metal", "EXCHANGE": "Exchange",
            "PRICE_OPEN_USD_PER_OZ": "Open", "PRICE_CLOSE_USD_PER_OZ": "Close",
            "PRICE_HIGH_USD_PER_OZ": "High", "PRICE_LOW_USD_PER_OZ": "Low",
        })
        st.dataframe(raw_df, use_container_width=True)

    csv_data = generate_csv()
    st.download_button(
        "Download Complete Dataset (CSV)",
        data=csv_data,
        file_name="benchmark_minerals_pricing.csv",
        mime="text/csv",
    )

    st.caption(f"Showing {len(filtered):,} records")

    st.divider()
    st.subheader("Live Price Lookup")

    @st.fragment
    def live_price_lookup():
        available_commodities = ["Gold", "Palladium", "Platinum", "Silver"]
        live_col1, live_col2, _ = st.columns([3, 3, 4])
        with live_col1:
            lookup_metal = st.selectbox("Commodity", available_commodities)
        with live_col2:
            st.write("")
            st.write("")
            fetch_btn = st.button("Get Latest Price", key="fetch_live_btn")
        st.markdown(
            '<style>#root div[data-testid="stButton"]:has(button[key="fetch_live_btn"]) button '
            '{background-color:#29B5E8 !important;color:white !important;border:none !important;}</style>',
            unsafe_allow_html=True,
        )
        if fetch_btn:
            with st.spinner(f"Fetching live {lookup_metal} price..."):
                try:
                    result = session.call(
                        "BENCHMARKMINERALS_DB.PUBLIC.FETCH_LIVE_METAL_PRICE",
                        lookup_metal,
                    )
                    data = json.loads(result) if isinstance(result, str) else result
                    if data.get("price"):
                        price = data["price"]
                        time_str = data.get("timestamp", "N/A")
                        exchange = data.get("exchange", "N/A")
                        st.markdown(
                            f"""
<div style="background:#f8f9fb;border:1px solid #dfe3e8;border-radius:10px;padding:20px 28px;margin-top:8px;">
  <div style="display:flex;gap:48px;flex-wrap:wrap;">
    <div><span style="color:#6b7280;font-size:0.85rem;">Material</span><br/><span style="font-size:1.25rem;font-weight:600;">{lookup_metal}</span></div>
    <div><span style="color:#6b7280;font-size:0.85rem;">Price</span><br/><span style="font-size:1.25rem;font-weight:600;color:#16a34a;">${price:,.2f} USD/oz</span></div>
    <div><span style="color:#6b7280;font-size:0.85rem;">Time</span><br/><span style="font-size:1.25rem;font-weight:600;">{time_str}</span></div>
    <div><span style="color:#6b7280;font-size:0.85rem;">Exchange</span><br/><span style="font-size:1.25rem;font-weight:600;">{exchange}</span></div>
  </div>
</div>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(data.get("error", "Could not retrieve price."))
                except Exception as e:
                    st.error(f"Error: {e}")

    live_price_lookup()
