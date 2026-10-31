# CricInsight — Conversational Cricket Performance Analysis & Tournament Platform

CricInsight is a production-grade NLP-powered cricket analytics and tournament management platform. It allows users to ask questions in plain English and receive deterministically calculated statistics, interactive Recharts visualizations, and evidence-grounded natural-language explanations without numerical hallucination. In addition, CricInsight features a full-fledged **Local Tournament Arena** with both **Live Ball-by-Ball Digital Scoring** and **Quick Scorecard Entry**.

---

## Core Architectural Principle

> **NLP understands the question. Retrieval finds the evidence. Python calculates the statistics deterministically. The language model explains the verified results.**
>
> *The language model is NEVER permitted to invent cricket statistics or independently calculate authoritative numerical results.*

---

## Technology Stack

- **Frontend (`frontend_react`)**: Modern React 18, Vite, Tailwind CSS, Recharts, Lucide Icons. Designed to human UI/UX specialist standards (`frontenddev`).
  - **Analytics Studio**: Split-view conversational search with format filters, KPI cards, and dynamic Recharts.
  - **Local Tournament Arena**: League management, live Net Run Rate (NRR) Points Table, Orange & Purple Cap leaderboards.
  - **Live Scorepad**: Ball-by-ball digital scorer with runs keypad, dismissal modal, and automatic strike rotation.
  - **Player Comparison Studio**: Dedicated head-to-head comparison workspace.
  - **System Observability**: Integrated benchmark accuracy and dataset coverage explorer.
- **Backend API**: Python 3.13, FastAPI, Pydantic v2.
- **Data Analytics Engine**: Python + Pandas + NumPy (deterministic mathematical formulas).
- **Primary NLP Provider**: Google Gemini API via official `google-genai` SDK.
- **Local Fallback NLP**: Qwen 2.5 running locally via Ollama.
- **Primary Database**: PostgreSQL 16 with `pgvector` extension and Full-Text Search.
- **Analytical Mirror**: DuckDB in-process columnar mirror with 60+ curated matches and 14,496+ deliveries indexed.
- **Data Source**: Authoritative Cricsheet JSON match and ball-by-ball records.

---

## Quick Start (Windows Root Launchers)

For convenience, double-click or run from repository root:

```bash
# 1. Start FastAPI Backend (http://127.0.0.1:8000)
.\start_backend.bat

# 2. In a second terminal, start React Frontend (http://localhost:3000)
.\start_frontend.bat
```

---

## Getting Started (Manual Setup)

### 1. Backend Setup & Virtual Environment

```bash
cd NLP_microproject/cricinsight/backend
python -m venv .venv
.\.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

#### Environment Variables (`.env`)

Configure `backend/.env`:

```env
# Primary NLP Provider (Google Gemini)
LLM_PRIMARY_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GEMINI_CONNECT_TIMEOUT=3
GEMINI_TOTAL_TIMEOUT=10

# Local Fallback Provider (Qwen via Ollama)
LLM_FALLBACK_PROVIDER=qwen
LLM_FALLBACK_ENABLED=true
QWEN_BASE_URL=http://localhost:11434
QWEN_MODEL=qwen2.5:3b-instruct

# Storage & Ingestion Paths
RAW_DATA_DIR=data/cricsheet
DUCKDB_PATH=data/cricinsight.duckdb
API_HOST=127.0.0.1
API_PORT=8000
```

---

### 2. Automated Cricsheet Dataset Download & Ingestion

To automatically download official Cricsheet archives (IPL, ODIs, T20Is) and populate the database:

```bash
# Download and ingest curated modern IPL matches
python scripts/download_cricsheet_data.py --pack ipl --limit 60 --since 2020-01-01

# Or download and ingest ODIs
python scripts/download_cricsheet_data.py --pack odis --limit 50
```

This downloads `people.csv` player registry, extracts high-value matches, and idempotently loads tens of thousands of deliveries into the database.

---

### 3. Local Tournament & Grassroots Match Scoring

CricInsight supports grassroots and club tournaments through two distinct modes:

1. **Mode 1: Live Ball-by-Ball Scoring Pad**:
   - Interactive runs keypad: `[ 0 ] [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 6 ] [ Wd ] [ Nb ] [ Bye ] [ Legbye ] [ Wicket ]`.
   - Automatic strike rotation: on singles/triples and after 6 legal balls at over boundaries.
   - Wicket modal tracking dismissal kind (bowled, caught, run out, lbw, stumped) and incoming batter.
   - Real-time Current Run Rate (CRR) and live over progression ticker.

2. **Mode 2: Quick Scorecard Entry (Summary Mode)**:
   - 60-second summary form for recording completed local games.
   - Team total scores, overs, wickets, and key individual player batting/bowling figures.

3. **Dynamic Standings & Leaderboards**:
   - **Points Table**: Automatically calculated with Net Run Rate:
     $$\text{NRR} = \left(\frac{\text{Runs Scored}}{\text{Overs Faced}}\right) - \left(\frac{\text{Runs Conceded}}{\text{Overs Bowled}}\right)$$
   - **Orange Cap**: Top run scorers, batting averages, strike rates, 50s, 100s.
   - **Purple Cap**: Top wicket takers, bowling economy rates, best figures.

---

### 4. Running Tests

#### Backend Test Suite (38 tests)
```bash
cd NLP_microproject/cricinsight/backend
.\.venv\Scripts\pytest -v
```

#### Frontend Test Suite (7 tests)
```bash
cd NLP_microproject/cricinsight/frontend_react
npm test
```

---

## API Endpoints Reference

### Core Analytics & NLP
- `POST /api/chat/query`: Main conversational query pipeline with deterministic analytics and grounded insights.
- `GET /api/health`: Health status and database match/delivery counts.
- `GET /api/dataset/coverage`: Ingested formats, match counts, and team listings.
- `GET /api/players/search?q=...`: Autocomplete player entity search.

### Local Tournament Arena
- `GET /api/tournaments` & `POST /api/tournaments`: List or create local tournaments.
- `GET /api/tournaments/{id}`: Detailed tournament fixtures, teams, and standings.
- `POST /api/tournaments/{id}/teams`: Register a team and squad roster.
- `POST /api/tournaments/{id}/matches`: Schedule a match fixture.
- `POST /api/tournaments/matches/{match_id}/scorecard`: Summary mode scorecard recording.
- `POST /api/tournaments/matches/{match_id}/ball`: Live ball-by-ball delivery logging.
- `GET /api/tournaments/{id}/standings`: Points table with Net Run Rate (NRR).
- `GET /api/tournaments/{id}/leaderboard`: Orange Cap and Purple Cap rankings.

### Observability & Evaluation
- `GET /api/evaluation/summary`: Benchmark accuracy and exact-match rates.
- `POST /api/evaluation/run`: Trigger on-demand benchmark suite execution.
- `GET /api/evaluation/providers`: Active status of Gemini, Qwen, and deterministic fallbacks.
