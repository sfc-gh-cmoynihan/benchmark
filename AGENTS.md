# Benchmark Minerals Intelligence

## Project Overview

Snowflake data product: critical minerals pricing dashboard with Cortex AI (Agent, Search, Analyst), Native App, and Marketplace listing.

**Snowflake Account:** IE_DEMO10 (AWS EU-West-1), Database: BENCHMARKMINERALS_DB

## Quick Start

```bash
# Clone
git clone https://github.com/sfc-gh-cmoynihan/benchmark.git
cd benchmark

# Deploy the Streamlit app to Snowflake
snow streamlit deploy --replace --connection <your_connection>
```

## Project Structure

| Path | Purpose |
|------|---------|
| `bmd_streamlit_app.py` | Provider Streamlit dashboard (deployed to SiS) |
| `snowflake.yml` | Snow CLI deployment config |
| `ask_benchmark_spec.json` | Cortex Agent specification (4 tools) |
| `battery_critical_minerals_pricing_sv.yaml` | Semantic View YAML |
| `manifest.yml` | Marketplace listing manifest |
| `BENCHMARK_DASHBOARD.ipynb` | Shared notebook |
| `native_app/` | Native App package (manifest, setup.sql, consumer Streamlit) |
| `analyst_reports/` | 10 analyst PDFs indexed by Cortex Search |

## Key Snowflake Objects

| Object | FQN |
|--------|-----|
| Database | `BENCHMARKMINERALS_DB` |
| Streamlit App | `BENCHMARKMINERALS_DB.PUBLIC.BENCHMARK_MINERALS_DASHBOARD` |
| Cortex Agent | `BENCHMARKMINERALS_DB.PUBLIC.ASK_BENCHMARK` |
| Cortex Search | `BENCHMARKMINERALS_DB.UNSTRUCTURED.ANALYST_REPORTS_SEARCH` |
| Semantic View (Pricing) | `BENCHMARKMINERALS_DB.PUBLIC.BATTERY_CRITICAL_MINERALS_PRICING_SV` |
| Semantic View (Indices) | `BENCHMARKMINERALS_DB.PUBLIC.MARKET_INDICES_SV` |
| Live Price Proc | `BENCHMARKMINERALS_DB.PUBLIC.FETCH_LIVE_METAL_PRICE` |
| App Package | `BENCHMARK_MINERALS_NATIVE_APP_PKG` |
| Marketplace Listing | `BENCHMARK_MINERALS_APP_LISTING` |

## Commands

### Lint & Validate

```bash
# Validate the Streamlit app syntax
python3 -m py_compile bmd_streamlit_app.py

# Validate the semantic view YAML
python3 -c "import yaml; yaml.safe_load(open('battery_critical_minerals_pricing_sv.yaml'))"

# Validate the agent spec JSON
python3 -c "import json; json.load(open('ask_benchmark_spec.json'))"
```

### Deploy

```bash
# Streamlit app
snow streamlit deploy --replace --connection <your_connection>

# Native App package (upload to stage, then create version)
# See README.md for full instructions
```

### Test

```bash
# Test Cortex Agent
snow sql -q "SELECT SNOWFLAKE.CORTEX.AGENT('BENCHMARKMINERALS_DB.PUBLIC.ASK_BENCHMARK', 'What is the latest gold price?')" --connection <your_connection>

# Test Cortex Search
snow sql -q "SELECT * FROM TABLE(BENCHMARKMINERALS_DB.UNSTRUCTURED.ANALYST_REPORTS_SEARCH('gold outlook', 3))" --connection <your_connection>

# Test Semantic View
snow sql -q "SELECT * FROM BENCHMARKMINERALS_DB.PUBLIC.BATTERY_CRITICAL_MINERALS_PRICING LIMIT 5" --connection <your_connection>
```

## Connection

Uses Snow CLI connection. Set up via:
```bash
snow connection add
```

Or use an existing connection from `~/.snowflake/connections.toml`.
