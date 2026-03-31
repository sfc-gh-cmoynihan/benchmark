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

## Cortex Search

10 analyst reports from leading financial institutions are parsed, chunked, and indexed using Cortex Search for RAG-based retrieval.

**Reports indexed:**
- Goldman Sachs — Gold $5,000 thesis (2026)
- World Gold Council — 2026 Outlook
- WisdomTree — Gold Outlook Q2 2026 (US & Global)
- Sprott — Gold Outlook 2026
- Heraeus — Precious Metals Forecast 2026
- WPIC — Platinum Outlook 2026
- HDFC Securities — Precious Metals Outlook 2026
- SSGA — Monthly Gold Monitor (March 2026)
- VTC Research — Gold Price Update 2026

PDFs are processed with `PARSE_DOCUMENT`, split into chunks, and stored in `BENCHMARKMINERALS_DB.UNSTRUCTURED.DOCS_CHUNKS_TABLE`. The Cortex Search service (`ANALYST_REPORTS_SEARCH`) enables natural language queries across all reports, powering the `search_analyst_reports` tool in the Cortex Agent.

## Native App

The entire data product is packaged as a Snowflake Native App for distribution via the Marketplace.

### What's in the Package

The listing manifest (`manifest.yml`) uses **declarative sharing** to share data and AI services without copying data:

| Shared Object | Type |
|---------------|------|
| 8 Tables | Pricing, indices, mining, supply chain, manufacturers, analyst reports |
| 2 Semantic Views | `BATTERY_CRITICAL_MINERALS_PRICING_SV`, `MARKET_INDICES_SV` |
| 1 Cortex Search Service | `ANALYST_REPORTS_SEARCH` |
| 1 Cortex Agent | `BENCHMARK_MINERALS_AGENT` (4 tools) |
| 1 Notebook | `BENCHMARK_DASHBOARD.ipynb` |

### App Package Structure

The app package (`native_app/`) contains:

- **`manifest.yml`** — App version, setup script, default Streamlit
- **`scripts/setup.sql`** — Creates an `APP_PUBLIC` role, a `CORE` schema with views over `SHARED_DATA`, and deploys the consumer Streamlit dashboard
- **`code_artifacts/streamlit/streamlit_app.py`** — Consumer-facing dashboard that queries data through the `CORE` schema views
- **`readme.md`** — Consumer-facing documentation

### Consumer Experience

When a consumer installs the app, `setup.sql` runs automatically:

1. Creates application role `APP_PUBLIC`
2. Creates `CORE` schema with views over the shared data (e.g. `CORE.BATTERY_CRITICAL_MINERALS_PRICING`)
3. Deploys the Streamlit dashboard (`APP_UI.BENCHMARK_MINERALS_DASHBOARD`)
4. Grants all permissions to `APP_PUBLIC`

Consumers can query shared tables directly or use the built-in Streamlit dashboard.

## Marketplace Listing

The Native App is published to the Snowflake Marketplace as an external listing with cross-cloud auto-fulfillment:

| Property | Value |
|----------|-------|
| **Listing** | `BENCHMARK_MINERALS_APP_LISTING` |
| **Type** | External (Marketplace) |
| **Fulfillment** | `SUB_DATABASE_WITH_REFERENCE_USAGE` |
| **Provider** | IE_DEMO10 — AWS EU-West-1 (Ireland) |
| **Consumers** | AWS US-West-2 (Oregon), Azure West-EU (Netherlands) |

Published once from Ireland — Snowflake handles replication to all consumer regions automatically.

## Key Snowflake Features

| Feature | Usage |
|---------|-------|
| **Native Apps** | Application package with Streamlit UI, setup scripts, shared data |
| **Declarative Sharing** | Tables, Semantic Views, Cortex Search, Agent — shared without copying data |
| **Cortex Analyst** | Natural language queries via Semantic Views |
| **Cortex Search** | 10 analyst PDFs indexed for RAG retrieval |
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
