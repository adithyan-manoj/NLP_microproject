# CricInsight — Architectural Blueprint & System Design

## 1. Executive Summary & Core Principle

**CricInsight** is an NLP-powered conversational cricket performance analysis system. Users can query player and match statistics in natural language and receive deterministically calculated metrics, interactive visualizations (`fl_chart`), and evidence-grounded natural-language explanations.

### Cardinal Architectural Rule:
> **NLP understands the question. Retrieval finds the evidence. Python calculates the statistics deterministically. The language model explains the verified results.**
> 
> *The language model is NEVER permitted to invent cricket statistics or independently calculate authoritative numerical results.*

```mermaid
flowchart TD
    User([User in React App]) -->|Natural Language Query| API[FastAPI /api/chat/query]
    API --> NLP[NLP Understanding Engine - Slide 4]
    NLP --> ProviderMgr{Provider Manager}
    ProviderMgr -->|Primary| Gemini[Google Gemini 2.5 Flash]
    ProviderMgr -->|Local Fallback 429/Timeout| Qwen[Local Qwen via Ollama on RTX 4050]
    ProviderMgr -->|Offline Resilience| Deterministic[Deterministic Rule Parser]
    
    ProviderMgr --> IntentSchema[Validated Canonical IntentSchema]
    IntentSchema --> Coref[Conversation Context & Coreference]
    Coref --> EntityRes[Entity & Format Resolution against Database]
    EntityRes --> ConfEval[Calibrated Multi-Tier Confidence Evaluator]
    
    ConfEval --> AnalyticsEngine[Deterministic Python Analytics Engine]
    AnalyticsEngine --> DB[(PostgreSQL 16 + pgvector / DuckDB Mirror)]
    DB --> VerifiedStats[Authoritative Computed Metrics]
    
    API --> RAG[Hybrid Knowledge Retriever]
    RAG --> KnowledgeChunks[(knowledge_chunks: pgvector + FTS)]
    KnowledgeChunks --> DomainRules[Cricket Rules, Formulas, Cricsheet Caveats]
    
    VerifiedStats --> ChartSelector[Deterministic Chart Selector]
    ChartSelector --> ChartSpec[Recharts Interactive Specification]
    
    VerifiedStats & DomainRules --> InsightGen[Evidence-Grounded Insight Generator]
    InsightGen --> GroundedText[Verified Natural Language Explanation]
    
    GroundedText & ChartSpec & VerifiedStats --> ReactUI[React 18 Sports Workspace]
    ReactUI --> Studio[Analytics Studio & Split Canvas]
    ReactUI --> TourArena[Local Tournament Arena & Live Scorepad]
    ReactUI --> HeadToHead[Head-to-Head Comparison Studio]
    ReactUI --> Observability[System Observability Center]
```

---

## 2. Technology Stack

| Layer | Technology | Role & Justification |
|---|---|---|
| **Frontend** | Flutter (Dart) | Modern, responsive cross-platform conversational interface |
| **Data Visualization** | `fl_chart` | Native Flutter chart rendering (line charts, bar charts, comparison plots) |
| **API & Business Logic** | Python 3.13 + FastAPI + Pydantic v2 | High-throughput asynchronous orchestration and strict contract validation |
| **Primary NLP** | Google Gemini (`google-genai` SDK) | Query interpretation, entity extraction, and grounded explanation |
| **Local Fallback NLP** | Qwen 2.5 via Ollama | Local on-device NLP fallback running on NVIDIA RTX 4050 GPU |
| **Primary Database** | PostgreSQL 16 + `pgvector` | Authoritative relational match & ball-by-ball store + vector search |
| **Local Columnar Mirror** | DuckDB | In-process analytical mirror for seamless zero-downtime test resilience |
| **Data Analytics Engine** | Python + Pandas + NumPy | 100% deterministic mathematical calculations for all metrics |
| **Source Dataset** | Official Cricsheet JSON | Single authoritative source of truth for match and delivery records |

---

## 3. Centralized Dual-Provider LLM Fallback Policy

```mermaid
stateDiagram-v2
    [*] --> GeminiAttempt: Incoming User Query
    GeminiAttempt --> Validation: Gemini 200 OK (< 10s)
    GeminiAttempt --> QwenFallback: 429 Rate Limit / Timeout / Net Err
    QwenFallback --> Validation: Qwen 200 OK (< 20s)
    QwenFallback --> DeterministicFallback: Ollama Unreachable / Error
    DeterministicFallback --> Validation: Regex & Rule Matching
    Validation --> DatabaseExecution: Pydantic Schema Valid
    Validation --> UserClarification: Ambiguous Entity / Low Confidence
```

### SLA & Bounded Timeouts:
- **`GEMINI_CONNECT_TIMEOUT`**: 3 seconds
- **`GEMINI_TOTAL_TIMEOUT`**: 10 seconds
- **`QWEN_TOTAL_TIMEOUT`**: 20 seconds
- **`LLM_MAX_TOTAL_DEADLINE`**: 32 seconds (hard request boundary)
- **Circuit Breaker**: Trips after 3 consecutive provider failures with a 60s cooldown, bypassing slow timeouts.

---

## 4. Grounded Hybrid RAG Architecture

Hybrid RAG retrieves cricket domain knowledge without contaminating authoritative numerical analytics:
1. **Full-Text Keyword Search**: PostgreSQL `tsvector` with `plainto_tsquery` and `ts_rank_cd`.
2. **Vector Similarity**: `pgvector` Euclidean/Cosine embedding distance.
3. **Reciprocal Rank Fusion (RRF)**:
   $$\text{RRF}(d) = \sum_{m \in \{\text{vector}, \text{fts}\}} \frac{1}{60 + \text{rank}_m(d)}$$
4. **Authority Separation**: Text from RAG is strictly supplementary (explaining scoring conventions, rules, and metric formulas). It is forbidden from overriding database counts or computed runs.
