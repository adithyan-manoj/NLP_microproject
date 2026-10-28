# CricInsight — NLP-Powered Cricket Performance Analysis & RAG System

> **Comprehensive System Documentation, Architecture, Setup Guide, Dataset Instructions & Roadmap**

---

## 1. Project Overview & Objective

**CricInsight** is an end-to-end cricket analytics and Retrieval-Augmented Generation (RAG) platform. Unlike generic LLM chatbots that hallucinate sports statistics or traditional analytics dashboards that require navigating dozens of manual drop-down menus, CricInsight enables users to ask cricket questions in **plain English**.

The platform interprets conversational questions, maps them to structured query entities, executes high-speed parameterized OLAP queries on a local DuckDB database comprising **732,536+ ball-by-ball deliveries**, computes mathematical cricket metrics, renders adaptive interactive charts, and synthesizes grounded analytical explanations.

---

## 2. System Architecture & Query Pipeline

```
                                  USER QUERY
             ("Compare Rohit Sharma and Virat Kohli in T20" or
              "Who won India vs Pakistan 2026 T20?" or
              "How has David Warner performed against Pakistan in ODIs?")
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 1. NLP Understanding & Router  │
                      │ (app/services/nlp_service.py)  │
                      └────────────────────────────────┘
                                      │
       Classifies intent & extracts: Players, Teams, Format, Opponent, Year, Recent N
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 2. DuckDB In-Memory OLAP RAG   │
                      │ (app/database/db.py)           │
                      └────────────────────────────────┘
                                      │
       Executes parameterized SQL over 732k deliveries & 1,656 matches (read-only)
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 3. Cricket Statistical Engine  │
                      │ (app/services/cricket_data.py) │
                      └────────────────────────────────┘
                                      │
       Computes: Runs, Batting Avg, Strike Rate, Std Dev (σ), Boundaries, 50s/100s, Scorecards
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 4. Grounded Synthesis / LLM    │
                      │ (app/services/insight_service) │
                      └────────────────────────────────┘
                                      │
       Gemini / Grounded RAG generates evidence-based insights strictly from computed math
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │ 5. Dynamic React + Recharts UI │
                      │ (cricinsight/frontend)         │
                      └────────────────────────────────┘
       Renders KPI Cards, Comparison Cards, Line/Bar Charts, Scope Badges & Insights
```

---

## 3. Technology Stack & Component Responsibilities

| Component | Technology | Exact Responsibility |
|---|---|---|
| **Frontend** | React 18 (Vite) + Tailwind CSS | High-contrast conversational interface, prominent search input, suggestions chips, loading skeletons, error states |
| **Data Visualization** | Recharts (React) | Responsive Line charts (innings progression) and grouped Bar charts (player comparisons and match scorecards) |
| **Backend API** | Python 3.9+ with FastAPI & Uvicorn | RESTful API (`/api/analyze`, `/api/health`, `/api/players`), entity routing, and response serialization |
| **Analytical Database** | DuckDB (Columnar In-Process OLAP) | Sub-10ms SQL aggregations directly on 732,536 deliveries without running a heavy database server |
| **Data Ingestion** | Python (`setup_db.py`) | Normalizes raw Cricsheet JSON files and `people.csv` into tabular relational tables |
| **Statistical Methods** | Pandas, NumPy, Python Standard Library | Batting averages (with not-out accounting), strike rates, standard deviation ($\sigma$) for consistency, rolling averages |
| **LLM / Grounded RAG** | Google Gemini API (`gemini-2.5-flash`) | NLP intent extraction and analytical synthesis strictly based on retrieved DuckDB numbers |
| **Deterministic Fallback** | Regular Expressions & Token Spans | Zero-latency fallback for NLP entity matching and template-based insight generation |
| **Testing** | pytest + Vitest | Unit tests for statistical calculations, API routes, database integrity, and React components |

---

## 4. Current State: What Has Been Implemented

### 4.1 Frontend (`cricinsight/frontend`)
- **Prominent Natural Language Input**: Polished Tailwind-styled query input with glowing focus states, clear button, animated submit button, and keyboard IME composition protection.
- **Dynamic Context Routing**:
  - **Single-Player Mode**: Innings run-by-run progression line chart, KPI stat cards (Runs, Average, Strike Rate, High Score, Standard Deviation Consistency, Boundaries).
  - **Player Comparison Mode**: Grouped multi-metric comparison cards (Runs, Avg, Strike Rate, 100s, 50s, Consistency) and a comparative grouped bar chart.
  - **Match Scorecard Mode**: Team innings runs, wickets lost, overs, top batters, top bowlers, and match result badges.
- **Resolved Query Scope Badges**: Displays tags for extracted player names, format, opponent, date ranges, and analysis type.
- **Evidence-Based Insight Panel**: Summarizes the mathematical observations and milestones without fictional commentary.
- **System Health Monitor**: Live badge showing DuckDB status, total match count, and total delivery count.

### 4.2 Backend (`cricinsight/backend`)
- **Intent Router**: Supports `player_analysis`, `player_comparison`, and `match_analysis`.
- **Comprehensive Player Alias Engine**: Contains aliases and abbreviations for international players across India, Australia, Pakistan, England, South Africa, New Zealand, West Indies, Sri Lanka, and Afghanistan. Dynamically scans the database for any additional names.
- **Greedy Non-Overlapping Token Matcher**: Prevents sub-string collisions (e.g., `"David Warner"` will not falsely trigger `"David"`).
- **Safe Context Carryover**: Follow-up queries only inherit past players if pronouns (`"he"`, `"his"`, `"their"`) or relative phrases (`"last 5 matches"`) are present.
- **Database Access Layer**: Parameterized SQL queries using context managers with `read_only=True` to guarantee thread safety and prevent SQL injection.

---

## 5. Dataset Information & How to Obtain It

The project uses official open-source cricket data provided by **[Cricsheet](https://cricsheet.org/)**.

### 5.1 Where to Get the Data
1. **Match Data (JSON format)**:
   - Download the match archives directly from Cricsheet:
     - **ODIs**: `https://cricsheet.org/downloads/odis_json.zip`
     - **T20 Internationals**: `https://cricsheet.org/downloads/t20s_json.zip`
     - **IPL / Franchise Leagues**: `https://cricsheet.org/downloads/ipl_json.zip`
2. **Player Registry (`people.csv`)**:
   - Download the official Cricsheet People register:
     - `https://cricsheet.org/downloads/people.csv`
   - This maps player unique IDs to canonical names and aliases.

### 5.2 Target Storage Location
Place raw files in the backend data directory:
```
cricinsight/backend/data/
├── cricsheet/          <-- Extracted match JSON files (e.g., 1000887.json)
├── people.csv          <-- Player register CSV
└── cricinsight.duckdb  <-- Generated automatically by setup_db.py
```

> **Note on Version Control (`.gitignore`)**:
> Due to the large volume of data (700k+ rows, 40MB+ database), `.duckdb`, `*.csv`, `*.json`, and `cricsheet/` are excluded from Git to keep the repository lightweight. New collaborators must run the ingestion script locally.

---

## 6. Step-by-Step Setup & Development Guide

Follow these exact steps to set up and run the project from a fresh clone:

### Step 1: Clone the Repository
```bash
git clone <YOUR_REPO_URL>
cd "NLP project"
```

### Step 2: Set Up Python Backend Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
pip install -r cricinsight/backend/requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file inside `cricinsight/backend/`:
```bash
cp cricinsight/backend/.env.example cricinsight/backend/.env
```
Open `cricinsight/backend/.env` and optionally set your Gemini API key:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: If `GEMINI_API_KEY` is left blank, the system automatically runs on its built-in deterministic statistical engine and regex parser).*

### Step 4: Populate or Ingest the Dataset
If `cricinsight/backend/data/cricinsight.duckdb` is not present, run the ingestion pipeline:
```bash
PYTHONPATH=cricinsight/backend ./venv/bin/python3 cricinsight/backend/app/ingestion/setup_db.py
```
This script downloads/reads Cricsheet JSON files, normalizes deliveries into tabular structures, indexes canonical names, and creates `cricinsight.duckdb`.

### Step 5: Run Backend Tests
Ensure all 15 backend tests pass:
```bash
PYTHONPATH=cricinsight/backend ./venv/bin/pytest cricinsight/backend/tests
```

### Step 6: Start the FastAPI Backend Server
```bash
source venv/bin/activate
PYTHONPATH=cricinsight/backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

### Step 7: Set Up and Run the React Frontend
Open a new terminal window:
```bash
cd cricinsight/frontend

# Install dependencies
npm install

# Run frontend tests
npm test

# Start the Vite development server
npm run dev
```
Open your browser at **`http://localhost:3000`**.

---

## 7. Known Issues, Limitations & Edge Cases

When taking over or continuing development, keep these known constraints in mind:

| Category | Current Behavior / Limitation | Recommended Future Improvement |
|---|---|---|
| **Bowling Inquiries** | The engine currently aggregates batting records (runs, strike rate, boundaries, dismissals). Bowling figures are extracted at the match-level, but career bowler comparisons (e.g., *"Compare Bumrah and Starc in ODIs"*) default to batting metrics. | Extend `query_player_innings` to detect if the player is primarily a bowler, and return wickets, economy rate, and bowling averages. |
| **Dataset Completeness** | The demo dataset focuses on international matches between 2015 and 2026. Very early historical matches (e.g. 1990s or early 2000s) are not present in the current local DuckDB file. | Download and ingest older Cricsheet archives if historical records across all decades are needed. |
| **Tie / Super Over Results** | Matches ending in ties or DLS rain-rule calculations currently show simple run/wicket difference summaries. | Parse the `info.outcome` block in Cricsheet JSON for official DLS method notes and Super Over results. |
| **Frontend Bundle Size** | Vite displays a chunk warning because Recharts and Lucide icons are bundled into a single chunk (>500 kB). | Implement code-splitting and dynamic `import()` in `vite.config.js` using `manualChunks`. |

---

## 8. Suggested Future Roadmap for Collaborators

1. **Phase 7: Comprehensive Bowling & All-Rounder Statistics**:
   - Add bowling metric calculations (`wickets_taken`, `economy_rate`, `bowling_average`, `maidens`).
   - Automatically toggle between "Batting View" and "Bowling View" in the UI depending on query intent.
2. **Phase 8: Match Situation & Venue Slicing**:
   - Support queries such as *"Kohli when chasing in Australia"* (innings 2 filtering + venue matching).
3. **Phase 9: Conversational Chat UI**:
   - Provide a persistent chat drawer on the side showing the conversational history and allowing users to click prior queries to restore state.
4. **Phase 10: Dockerization & Cloud Deployment**:
   - Add a `Dockerfile` and `docker-compose.yml` to package the FastAPI backend, DuckDB file, and Vite frontend for one-command deployment to Google Cloud Run or AWS.

---

## 9. Verification & Test Commands Quick Reference

```bash
# Backend unit tests (15 test cases)
PYTHONPATH=cricinsight/backend ./venv/bin/pytest cricinsight/backend/tests

# Frontend component tests (Vitest + React Testing Library)
cd cricinsight/frontend && npm test

# Production frontend build
cd cricinsight/frontend && npm run build
```

