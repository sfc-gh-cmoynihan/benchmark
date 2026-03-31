# Benchmark Minerals Intelligence

A complete Snowflake data product showcasing Native Apps, Cortex AI, and cross-cloud Marketplace deployment — built entirely with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code).

## What It Does

Benchmark Minerals Intelligence tracks daily pricing for critical minerals (lithium, cobalt, nickel, gold, platinum and more) across global exchanges. This project packages that data with AI-powered analytics into a single Native App distributed via the Snowflake Marketplace.

## Architecture

```
Provider (IE_DEMO10 — AWS Ireland)
├── BENCHMARKMINERALS_DB
│   ├── PUBLIC
│   │   ├── 8 Tables (pricing, indices, mining, supply chain, manufacturers, analyst reports)
│   │   ├── 2 Semantic Views (Cortex Analyst — natural language to SQL)
│   │   └── 1 Cortex Search Service (10 analyst PDFs, 731 chunks)
│   └── AGENT_SCHEMA
│       └── Cortex Agent (4 tools: pricing, indices, live prices, analyst search)
├── Streamlit Dashboard (interactive charts + embedded AI chat)
└── Native App Package → Marketplace Listing → Cross-cloud replication
```

## Key Snowflake Features

| Feature | Usage |
|---------|-------|
| **Native Apps** | Application package with Streamlit UI, setup scripts, shared data |
| **Declarative Sharing** | Tables, Semantic Views, Cortex Search, Agent — shared without copying data |
| **Cortex Analyst** | Natural language queries via Semantic Views |
| **Cortex Search** | 10 analyst PDFs from Goldman Sachs, WGC, Sprott, WPIC and others |
| **Cortex Agent** | Multi-tool AI analyst combining structured + unstructured data |
| **Streamlit in Snowflake** | Dashboard with agent chat sidebar and live price lookup |
| **External Access** | Live metal prices from MetalPriceAPI |
| **Marketplace** | Cross-cloud auto-fulfillment (AWS Ireland → AWS Oregon → Azure) |

## Project Structure

```
.
├── bmd_streamlit_app.py                 # Provider Streamlit app (deployed to SiS)
├── snowflake.yml                        # Snow CLI deployment config
├── manifest.yml                         # Marketplace listing manifest
├── ask_benchmark_spec.json              # Cortex Agent specification
├── battery_critical_minerals_pricing_sv.yaml  # Semantic View definition
├── BENCHMARK_DASHBOARD.ipynb            # Notebook (shared via app package)
├── Demo Script.md                       # Full demo walkthrough (~25 min)
├── Demo Script.pdf                      # PDF version of demo script
├── analyst_reports/                     # 10 analyst PDFs (indexed by Cortex Search)
├── native_app/
│   ├── manifest.yml                     # App package manifest
│   ├── readme.md                        # Consumer-facing readme
│   ├── scripts/setup.sql                # Creates CORE schema + views
│   └── code_artifacts/streamlit/
│       ├── streamlit_app.py             # Consumer Streamlit app
│       └── environment.yml              # Conda environment
└── pyproject.toml
```

## Deploying

### Streamlit App (Provider)

```bash
snow streamlit deploy --replace --connection <your_connection>
```

### Native App Package

Upload the `native_app/` directory to a stage and create the application package:

```sql
CREATE APPLICATION PACKAGE BENCHMARK_MINERALS_NATIVE_APP_PKG;
-- Upload native_app/* to the package stage, then:
ALTER APPLICATION PACKAGE BENCHMARK_MINERALS_NATIVE_APP_PKG
  ADD VERSION V1 USING '@stage_path';
```

## Built With

This entire project — data, AI, app, and distribution — was built through conversations with **Cortex Code (CoCo)**, Snowflake's AI-powered development CLI.
