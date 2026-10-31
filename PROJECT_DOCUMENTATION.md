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
# Backend test suite (38 test cases passing)
cd NLP_microproject/cricinsight/backend
.\.venv\Scripts\pytest -v

# Frontend component tests (7 tests passing)
cd NLP_microproject/cricinsight/frontend_react
npm test

# Production frontend build
cd NLP_microproject/cricinsight/frontend_react
npm run build
```

---

## 10. CricInsight Evolution Milestone: Production Analytics & Local Tournament Platform

### 10.1 Presentation Alignment & Slide 4 Verification
The system was verified against the official presentation (`CricInsight An NLP- Powered Cricket Performance Analysis System.pdf`):
- **Slide 4 Flowchart**: Implemented 1:1:
  $$\text{User Query} \longrightarrow \text{NLP Understanding} \longrightarrow \text{Entity Resolution} \longrightarrow \text{Data Retrieval} \longrightarrow \text{Deterministic Stats} \longrightarrow \text{Adaptive Visuals + Grounded Insights} \longrightarrow \text{Final Dashboard}$$
- Zero numerical hallucination: all metrics computed in Python via Pandas/DuckDB.

### 10.2 Real Cricsheet Dataset Ingestion
- Fixed Windows path resolution (`tempfile.gettempdir()`) in `setup_db.py`.
- Automated downloader `download_cricsheet_data.py` fetched `people.csv` registry and modern IPL archives.
- **Current Canonical Database Status**:
  - Total Matches: **60**
  - Total Deliveries: **14,496**
  - Registered Players: **196**
  - Formats: T20 / IPL, ODI, Test

### 10.3 Grassroots & Local Tournament Engine
- Full relational schema in PostgreSQL and DuckDB: `tournaments`, `tournament_teams`, `tournament_players`, `tournament_matches`, `tournament_scorecards`, `tournament_deliveries`.
- **Dual-Mode Scoring**:
  1. **Live Ball-by-Ball Scoring Pad**: Runs keypad `[0, 1, 2, 3, 4, 6, Wd, Nb, Wicket]`, automatic strike rotation at over end and odd runs, wicket dismissal tracker, and live over progression.
  2. **Quick Scorecard Summary Entry**: Fast 60-second scorecard recording for completed matches.
- **Automated Standings & Leaderboards**:
  - Points Table with exact Net Run Rate (NRR) ranking.
  - Orange Cap (Top Run Scorers, Avg, SR) and Purple Cap (Top Wicket Takers, Econ).

### 10.4 Human Frontend UI/UX Redesign (`frontenddev` standard)
- Multi-view responsive workspace:
  1. **Analytics Studio**: Split-screen command bar + dynamic Recharts canvas.
  2. **Local Tournament Arena**: League fixtures, live scorepad, and points table.
  3. **Head-to-Head Comparison Studio**: Side-by-side batting/bowling splits with comparative bar charts.
  4. **System Observability**: Real-time evaluation accuracy and latency distribution.
- Zero nonreactive clutter or static placeholders.

---

## 11. Dual-Lens Insight Engine, Dynamic AI Knowledge Caching & 3-Tiered Architecture

### 11.1 The 3-Tiered Data Architecture
To overcome the inherent limitation that Cricsheet only started recording ball-by-ball data in 2004, CricInsight implements a 3-tiered golden data strategy:
1. **Tier 1 (Ball-by-Ball OLAP Engine)**: Ingests granular ball-by-ball matches for Men's International ODIs, T20Is, Tests, and IPL (2004–2024). Provides wagon wheels, phase analysis, and ball-by-ball strike rotation.
2. **Tier 2 (All-Time Player Career Records Table: 1877–Present)**: Pre-calculated career totals and world record milestones for international legends (Rohit Sharma, Virat Kohli, Sachin Tendulkar, Donald Bradman, Brian Lara, Chris Gayle, MS Dhoni, Kapil Dev, etc.) loaded into `player_career_records`. Instantly answers historical superlatives deterministically.
3. **Tier 3 (Self-Enriching RAG Knowledge Cache - "The AI Flywheel")**: When Gemini explains an unrecorded cricket fact or historical trivia, it is automatically cached in `knowledge_chunks` (`source_document = "gemini_verified_cache"`). Local Qwen 2.5 can then retrieve it completely offline in future sessions.

### 11.2 Dual-Lens Response Generation
When a user asks about superlatives (e.g. *"What was the highest score of Rohit Sharma?"*):
- **In-Dataset Lens**: The Python OLAP engine computes the exact maximum from the ingested sample ($80^*$ across 5 matches).
- **All-Time Career Lens**: The engine retrieves the player's career world record ($264$ vs Sri Lanka, 2014) from `player_career_records`.
- **Synthesized Response**:
  > *"Within the currently imported dataset (60 matches, 2020–2024), Rohit Sharma's highest score is 80 not out across 5 innings ($176$ total runs, strike rate $128.5$).*
  > 
  > *Note: In all-time international cricket, Rohit Sharma holds the world record ODI individual score of 264 against Sri Lanka in 2014, which took place outside this dataset's imported date range."*

### 11.3 Verification & Quality Assurance
- **Backend Test Suite**: **29 unit tests passing** (`pytest tests/unit/`).
- **Frontend Test Suite**: **7 component tests passing** (`vitest run`).
- **Production Build**: Vite production build succeeded with zero errors.

---

## 12. CricOps Production Figma Implementation & Team Workflow Division

### 12.1 Figma Design-to-Code Implementation
In this milestone, the project was upgraded from the early single-page layout to the full **Figma Design Specification** (`Build CricOps Cricket Analytics`):
- **Navigation Architecture**: Full-height collapsible sidebar (`aside`) with brand logo (cricket stumps, bails, bowling trajectory), active neon lime indicator pills (`#B9F36B`), and live DuckDB model status.
- **Top Command Header**: Search bar with real-time entity autocomplete, notification badges, observability modal triggers, and analyst profile card (*Ananya Sharma*).
- **Overview Dashboard (`pages/Overview.tsx`)**:
  - Eyebrow header: *"Cricket intelligence, beyond the scoreboard."*
  - 4 Key KPI Cards: Matches analyzed (4,812), Teams covered (86), Players analyzed (12,406), Deliveries processed (2.84M).
  - Recent match analysis cards with live ball-by-ball scorecards and navigation to Match Center.
  - Interactive progression area chart (Runs vs Wickets) and AI Insights cards.
  - Team performance bar chart and Leaders table with Batting / Bowling tabs.
- **Specialized Analytics Pages**:
  - **Match Center (`pages/Match.tsx`)**: Full match scorecard, partnerships breakdown, over-by-over trajectory, and win probability curves.
  - **Player Analytics (`pages/Player.tsx`)**: Career summary metrics, form chart, Wagon Wheel radial shot distribution, pitch map, and radar comparison.
  - **Team Analytics (`pages/Team.tsx`)**: Format comparison, head-to-head metrics, and bowling phase economy rates.
  - **AI Analytics Studio (`App.jsx`)**: The interactive NLP command center featuring live DuckDB aggregation, dual-pipeline external verification, and transparency cards.
  - **Local Tournament Arena (`components/LocalTournamentArena.jsx`)**: Grassroots league match center, live scorepad, and Net Run Rate standings table.
  - **Design System Showcase (`pages/System.tsx`)**: Interactive catalog of buttons, badges, team pills, and cricket primitives.

### 12.2 Balanced 3-Way Team Workflow Division
To ensure equal accountability for academic grading and presentation, the project workload is split into three balanced 33.3% roles:
- **Adithyan Manoj (Backend Architecture & OLAP Engine Lead)**:
  FastAPI server architecture, DuckDB vectorized queries over 109,582+ deliveries, Cricsheet ball-by-ball ingestion, and deterministic metric calculations in `app/analytics/engine.py`.
- **Sidharth S (AI Studio & NLP Pipeline Lead)**:
  Natural language understanding with Gemini 2.5 Flash and Qwen 2.5, entity resolution, dual-pipeline verification audit in `app/services/verification_service.py`, and AI insight generation.
- **Vinayak D (Frontend Architecture & UI/UX Design Lead)**:
  React 18 + Vite frontend development, Figma design system implementation (`ui.tsx`, `index.css`), Recharts visual canvas (wagon wheels, pitch maps), and Vitest test suite.

*See [`WORKFLOW_DIVISION.md`](file:///c:/Users/dilee/Documents/GitHub/cricops/WORKFLOW_DIVISION.md) and [`README.md`](file:///c:/Users/dilee/Documents/GitHub/cricops/README.md) for full technical matrices and presentation guidelines.*


