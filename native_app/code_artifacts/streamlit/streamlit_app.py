import streamlit as st
import altair as alt
import pandas as pd
from snowflake.snowpark.context import get_active_session

session = get_active_session()

TABLE = "CORE.BATTERY_CRITICAL_MINERALS_PRICING"

st.markdown(
    """<style>
    div[data-testid="stHorizontalBlock"] {
        align-items: flex-end;
    }
    </style>""",
    unsafe_allow_html=True,
)

st.title(":chart_with_upwards_trend: Benchmark Minerals Intelligence")
st.subheader("Precious Metals & Critical Minerals Daily Pricing")


def load_filter_options():
    meta = session.sql(f"""
        SELECT MIN(ASSESSMENT_DATE) AS MIN_DATE, MAX(ASSESSMENT_DATE) AS MAX_DATE
        FROM {TABLE}
        WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL
    """).to_pandas()
    materials = session.sql(f"""
        SELECT DISTINCT MATERIAL FROM {TABLE}
        WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL ORDER BY MATERIAL
    """).to_pandas()["MATERIAL"].tolist()
    exchanges = session.sql(f"""
        SELECT DISTINCT EXCHANGE FROM {TABLE}
        WHERE PRICE_CLOSE_USD_PER_OZ IS NOT NULL ORDER BY EXCHANGE
    """).to_pandas()["EXCHANGE"].tolist()
    return meta["MIN_DATE"].iloc[0], meta["MAX_DATE"].iloc[0], materials, exchanges


min_date_val, max_date_val, all_metals, all_exchanges = load_filter_options()
min_date = pd.Timestamp(min_date_val).date()
max_date = pd.Timestamp(max_date_val).date()

date_col1, date_col2, metal_col, exchange_col = st.columns([1, 1, 1, 1])

with date_col1:
    date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with date_col2:
    date_to = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
with metal_col:
    selected_metal = st.selectbox("Material", ["All"] + all_metals)
with exchange_col:
    selected_exchange = st.selectbox("Exchange", ["All"] + all_exchanges)

selected_metals = all_metals if selected_metal == "All" else [selected_metal]
selected_exchanges = all_exchanges if selected_exchange == "All" else [selected_exchange]


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

    st.caption(f"Showing {len(filtered):,} records")

    st.divider()
    st.markdown("""
    ### Available Data Tables
    Access all data via the **CORE** schema:
    - `CORE.BATTERY_CRITICAL_MINERALS_PRICING` - Daily OHLC pricing
    - `CORE.MARKET_INDICES` - Market indices (base-100)
    - `CORE.BATTERY_SUPPLY_CHAIN` - Supply chain data
    - `CORE.MINING_OPERATIONS` - Mining operations
    - `CORE.MINERAL_PRICE_ASSESSMENTS` - Price assessments
    - `CORE.SUPPLY_DEMAND_FORECASTS` - Supply/demand forecasts
    - `CORE.BATTERY_CELL_MANUFACTURERS` - Cell manufacturers
    - `CORE.ANALYST_REPORT_CHUNKS` - Analyst reports
    """)
