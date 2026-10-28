MASTER BUILD PROMPT — CRICINSIGHT

NLP-Powered Cricket Performance Analysis System

Act as a senior full-stack engineer, data engineer, NLP engineer, data visualization specialist, and UI/UX designer. Build a complete, functional, maintainable application called CricInsight.

Do not build merely a static frontend or a chatbot that talks about cricket. Build a working end-to-end cricket analytics system in which natural-language questions are converted into structured queries, relevant cricket records are retrieved from a real dataset, statistics are calculated programmatically, charts are generated from those statistics, and explanations are grounded in the calculated results.

First inspect the existing workspace, files, dependencies, and project structure. Preserve working code where possible. Then implement the project incrementally, test it, and document how to run it.

---

PART 1 — PROJECT OBJECTIVE

1.1 Problem statement

Cricket analytics platforms provide statistics, match information, player records, and filtering options. However, users may need to navigate multiple filters, select players and formats, define time periods, select statistics, and interpret charts manually.

This creates an accessibility and usability problem for people who want to ask analytical questions without knowing how to operate a complex analytics interface.

CricInsight addresses this problem by enabling users to ask questions in natural language, such as:

- "How has Virat Kohli performed against Australia in ODIs during the last three years?"
- "Compare Rohit Sharma and Virat Kohli in T20 internationals."
- "Show Kohli's last 10 innings as a line chart."
- "How consistent has this player been?"
- "Which opponent has this player scored the most runs against?"
- "Is the player's recent form improving?"
- "Compare the batting performance of two players in the same format."
- "What about his last five matches?" — using the previous conversational context.

The system must translate these questions into structured requirements, retrieve the correct records, calculate the appropriate statistics, visualize the results, and explain the findings.

1.2 Core processing pipeline

Implement the following pipeline:

User question → NLP query understanding → entity and intent extraction → validation and date resolution → database query construction → cricket data retrieval → statistical analysis → adaptive chart selection → evidence-based insight generation → final dashboard.

Also implement a separate data ingestion pipeline for the demo environment:

Cricsheet data (JSON) → Python processing script → Flattened format → DuckDB local database file.

These two pipelines must work independently.

---

PART 2 — TECHNOLOGY STACK, MODELS, AND RESPONSIBILITIES

Use the following stack unless the existing project has a compelling, documented reason to retain a different compatible technology.

Component | Technology | Exact responsibility
---|---|---
Frontend | React (Vite) + Tailwind CSS | User interface, query input, chat history, statistics cards, charts, loading/error states
Backend | Python with FastAPI | REST API, validation, orchestration, database access, analysis coordination
NLP model API | Google Gemini API | Interpret natural-language cricket questions and return structured query parameters
Insight-generation model API | Google Gemini API | Explain already calculated statistics and patterns without inventing facts
Primary data source | Cricsheet | Downloadable cricket match and ball-by-ball data
Database | DuckDB | In-process columnar database for blazing-fast local OLAP queries on cricket data
Data processing | Python | Parse, normalize, and transform Cricsheet JSON into DuckDB tables
Data analysis | Pandas and NumPy | Group, aggregate, and calculate cricket performance metrics from DuckDB queries
Statistical methods | Python standard library, NumPy | Mean, standard deviation, rolling averages, trend analysis
Query interpretation fallback | Python rules and dictionaries | Handle common terms and recover from NLP API failures
API transport | REST with JSON | Communicate between React and FastAPI
Chart rendering | React "recharts" library | Render line charts, bar charts, and other statistical visualizations
Visualization selection | Python rule-based engine | Select an appropriate chart from the validated analysis intent and result schema
Configuration and secrets | Environment variables / ".env" | Store API keys outside source code
Testing | pytest and Vitest | Verify statistics, API behavior, data ingestion, and UI logic

2.1 Model/API responsibilities

Use the Gemini API for two distinct tasks. These are separate application functions, even if they use the same underlying model.

A. Query-understanding model

Input: "Compare Kohli and Rohit in ODIs against Australia since 2022."

Expected structured output:
{
  "players": ["Virat Kohli", "Rohit Sharma"],
  "opponent": "Australia",
  "format": "ODI",
  "start_date": "2022-01-01",
  "end_date": null,
  "analysis_type": "comparison",
  "metrics": ["runs", "batting_average", "strike_rate"],
  "chart_preference": "bar",
  "needs_clarification": false
}

The query-understanding model is responsible for extracting parameters into this exact schema. It must not retrieve or fabricate statistics.

B. Insight-generation model

Input: Calculated statistics, analysis metadata, and the actual observations.
Output: A concise, evidence-based explanation.

The model must use only supplied metrics and observations, avoid inventing reasons for performance changes, and return a safe fallback if the API is unavailable.

C. Model configuration

Use the official Google GenAI SDK. Read keys from "GEMINI_API_KEY". Keep the model configurable.

---

PART 3 — DATASET AND CRICSHEET INGESTION (DEMO SETUP)

3.1 Data source
Use Cricsheet JSON downloads. Since this is for a demo presentation, focus on a robust preprocessing script rather than a live scheduled updater.

3.2 Ingestion pipeline
Implement a Python script (`setup_db.py`) to run before starting the server:
1. Read Cricsheet JSON files from a local directory.
2. Extract match metadata, innings, deliveries, and player identifiers.
3. Normalize the hierarchical JSON into tabular formats suitable for OLAP.
4. Load the normalized data into a local DuckDB file (`cricinsight.duckdb`).

3.3 Database design (DuckDB Tables)
Design efficient tables for analytical queries:

Table: "matches"
Columns: match_id, date, match_type, competition, venue, team_1, team_2.

Table: "deliveries"
Columns: match_id, innings_number, batting_team, bowling_team, over_num, ball_num, batter, bowler, non_striker, batter_runs, extra_runs, is_wicket, dismissal_kind, player_dismissed.

Table: "players"
Columns: player_id, canonical_name, aliases.

---

PART 4 — NATURAL-LANGUAGE QUERY UNDERSTANDING

4.1 Supported query entities
Implement Pydantic schema extraction for players, opponent, format, dates, recent_n, analysis_type, metrics, and chart_preference.

4.2 Query normalization
Resolve aliases (e.g., "Kohli" -> "Virat Kohli"), format strings, and calculate relative dates using a Python normalization layer before hitting the database.

4.3 Safe query construction
The LLM must never generate arbitrary SQL. Map the validated Pydantic schema to parameterized DuckDB SQL queries or secure Pandas operations.

---

PART 5 — STATISTICAL ANALYSIS AND ALGORITHMS

Use Python, DuckDB SQL, Pandas, and NumPy to calculate statistics.

5.1 Core metrics
Calculate Total Runs, Batting Average, Strike Rate, Boundaries, Centuries/Half-Centuries, Wickets, and Economy Rate using correct cricket scoring conventions directly from the `deliveries` table.

5.2 Recent-form & Consistency
Implement a last-N-innings filter chronologically. Calculate Standard Deviation of innings scores to measure consistency.

5.3 Statistical correctness
Use actual records from DuckDB. Never substitute example values. Include sample sizes with all responses. Return "null" for missing data.

---

PART 6 — ADAPTIVE VISUALIZATION

6.1 Chart-generation architecture
FastAPI must return a validated JSON visualization specification. React and `recharts` will render it.

Example backend response:
{
  "chart_type": "line",
  "title": "Runs Across Selected Innings",
  "x_axis_label": "Innings",
  "y_axis_label": "Runs",
  "series": [
    { "name": "Virat Kohli", "data": [{"x": "Inn 1", "y": 45}, {"x": "Inn 2", "y": 82}] }
  ]
}

6.2 Chart selection rules
- Chronological performance -> Line chart
- Player comparison -> Grouped bar chart
- Distribution -> Histogram

---

PART 7 — EVIDENCE-BASED INSIGHT GENERATION

Pass the structured DuckDB/Pandas results to Gemini to generate a short, analytical summary highlighting trends, comparisons, and limitations based *only* on the provided math.

---

PART 8 — CONVERSATIONAL CONTEXT

Store structured query context (not raw text) to support follow-up questions like "What about his last 5 matches?" Allow the user to seamlessly modify the current filter scope.

---

PART 9 — BACKEND API DESIGN

Endpoints:
- "POST /api/analyze" — process NLP query, return stats, chart spec, and insights.
- "GET /api/players" — search canonical players.
- "GET /api/health" — system health.

---

PART 10 — REACT FRONTEND AND UI/UX

Build a modern, minimalist dashboard using React, Vite, and Tailwind CSS.
- Keep the query input prominent.
- Show the resolved query scope (so the user knows the AI understood the date/format).
- Render `recharts` responsive components.
- Include skeleton loaders for async API calls.
- Use a clean typography and contrast setup typical of high-quality UI wireframes.

---

PART 11 — SECURITY, RELIABILITY, AND PERFORMANCE

- Parameterize DuckDB queries to prevent SQL injection.
- Do not expose Gemini API keys in the React client.
- Provide graceful fallbacks if no data matches the query.

---

PART 12 — PROJECT STRUCTURE

cricinsight/
  frontend/
    package.json
    tailwind.config.js
    src/
      App.jsx
      components/
        QueryInput.jsx
        StatCards.jsx
        ChartRenderer.jsx
        InsightPanel.jsx
      services/
        api.js

  backend/
    requirements.txt
    .env
    app/
      main.py
      api/
      core/
      services/
        nlp_service.py
        cricket_data_service.py
        insight_service.py
      database/
        db.py (DuckDB connection manager)
      ingestion/
        setup_db.py (Parses Cricsheet JSON -> cricinsight.duckdb)

---

PART 13 — IMPLEMENTATION PLAN

Phase 1: Project setup (React Vite + FastAPI).
Phase 2: Data ingestion script (Parse JSON to DuckDB).
Phase 3: Statistical engine (DuckDB/Pandas aggregations).
Phase 4: Backend API and LLM integration (Pydantic intent extraction).
Phase 5: Frontend UI and recharts integration.
Phase 6: End-to-end testing and refinement for the demo.

Begin by inspecting the workspace, then implement Phase 1.