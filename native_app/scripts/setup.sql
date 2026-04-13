CREATE APPLICATION ROLE IF NOT EXISTS APP_PUBLIC;

CREATE OR ALTER VERSIONED SCHEMA APP_UI;
GRANT USAGE ON SCHEMA APP_UI TO APPLICATION ROLE APP_PUBLIC;

CREATE SCHEMA IF NOT EXISTS CORE;
GRANT USAGE ON SCHEMA CORE TO APPLICATION ROLE APP_PUBLIC;

CREATE VIEW IF NOT EXISTS CORE.BATTERY_CRITICAL_MINERALS_PRICING
  AS SELECT * FROM SHARED_DATA.BATTERY_CRITICAL_MINERALS_PRICING;
CREATE VIEW IF NOT EXISTS CORE.MARKET_INDICES
  AS SELECT * FROM SHARED_DATA.MARKET_INDICES;
CREATE VIEW IF NOT EXISTS CORE.BATTERY_SUPPLY_CHAIN
  AS SELECT * FROM SHARED_DATA.BATTERY_SUPPLY_CHAIN;
CREATE VIEW IF NOT EXISTS CORE.MINING_OPERATIONS
  AS SELECT * FROM SHARED_DATA.MINING_OPERATIONS;
CREATE VIEW IF NOT EXISTS CORE.MINERAL_PRICE_ASSESSMENTS
  AS SELECT * FROM SHARED_DATA.MINERAL_PRICE_ASSESSMENTS;
CREATE VIEW IF NOT EXISTS CORE.SUPPLY_DEMAND_FORECASTS
  AS SELECT * FROM SHARED_DATA.SUPPLY_DEMAND_FORECASTS;
CREATE VIEW IF NOT EXISTS CORE.BATTERY_CELL_MANUFACTURERS
  AS SELECT * FROM SHARED_DATA.BATTERY_CELL_MANUFACTURERS;
CREATE VIEW IF NOT EXISTS CORE.ANALYST_REPORT_CHUNKS
  AS SELECT * FROM SHARED_DATA.ANALYST_REPORT_CHUNKS;

GRANT SELECT ON VIEW CORE.BATTERY_CRITICAL_MINERALS_PRICING TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.MARKET_INDICES TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.BATTERY_SUPPLY_CHAIN TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.MINING_OPERATIONS TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.MINERAL_PRICE_ASSESSMENTS TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.SUPPLY_DEMAND_FORECASTS TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.BATTERY_CELL_MANUFACTURERS TO APPLICATION ROLE APP_PUBLIC;
GRANT SELECT ON VIEW CORE.ANALYST_REPORT_CHUNKS TO APPLICATION ROLE APP_PUBLIC;

CREATE OR REPLACE PROCEDURE CORE.CALL_ASK_BENCHMARK_AGENT(QUESTION VARCHAR, HISTORY VARCHAR)
  RETURNS VARCHAR
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('snowflake-snowpark-python', 'snowflake')
  HANDLER = 'run'
  EXECUTE AS CALLER
AS $$
import json

def run(session, question, history):
    from snowflake.core import Root
    from snowflake.core.cortex.lite_agent_service import CortexAgentService, AgentRunRequest

    root = Root(session)
    agent_svc = CortexAgentService(root)

    messages = []
    if history and history.strip() and history != '[]':
        try:
            hist = json.loads(history)
            for m in hist:
                messages.append({
                    "role": m["role"],
                    "content": [{"type": "text", "text": m["content"]}],
                })
        except Exception:
            pass

    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": question}],
    })

    request = AgentRunRequest(
        messages=messages,
        tools=[
            {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "minerals_pricing"}},
            {"tool_spec": {"type": "cortex_search", "name": "analyst_reports", "description": "Search analyst reports and research documents about precious metals and critical minerals forecasts, outlooks, and market analysis."}},
        ],
        tool_resources={
            "minerals_pricing": {
                "semantic_view": "BENCHMARKMINERALS_DB.PUBLIC.BATTERY_CRITICAL_MINERALS_PRICING_SV",
                "execution_environment": {"type": "warehouse", "warehouse": "ADHOC_WH"},
            },
            "analyst_reports": {
                "search_service": "BENCHMARKMINERALS_DB.PUBLIC.ANALYST_REPORTS_SEARCH",
                "max_results": 5,
            },
        },
        instructions={"system": "You are a helpful Benchmark Minerals Intelligence assistant that answers questions about precious metals and critical minerals pricing data. You have access to two tools: (1) minerals_pricing for querying structured pricing data, and (2) analyst_reports for searching analyst research reports and forecasts about metals markets. Use analyst_reports when users ask about forecasts, outlooks, predictions, analyst opinions, or market analysis reports."},
    )

    response = agent_svc.run(request)

    final_text = ""
    for event in response.events():
        evt_name = str(event.event)
        data = event.data
        if evt_name == "response":
            if isinstance(data, dict):
                parts = []
                for item in data.get("content", []):
                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))
                final_text = "\n".join(parts)
            break
        elif evt_name == "error":
            if isinstance(data, dict):
                return f"Agent error: {data.get('message', 'Unknown error')}"

    return final_text if final_text else "No response from agent."
$$;

GRANT USAGE ON PROCEDURE CORE.CALL_ASK_BENCHMARK_AGENT(VARCHAR, VARCHAR) TO APPLICATION ROLE APP_PUBLIC;

CREATE OR REPLACE STREAMLIT APP_UI.BENCHMARK_MINERALS_DASHBOARD
  FROM '/code_artifacts/streamlit'
  MAIN_FILE = '/streamlit_app.py';

GRANT USAGE ON STREAMLIT APP_UI.BENCHMARK_MINERALS_DASHBOARD TO APPLICATION ROLE APP_PUBLIC;
