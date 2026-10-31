# CricInsight — REST API Specifications

The CricInsight backend exposes clean, validated REST endpoints for conversational query orchestration, authoritative dataset inspection, and evaluation telemetry.

---

## 1. Chat Orchestration Endpoint

### `POST /api/chat/query`
Orchestrates natural-language question interpretation, coreference resolution, entity ground truth lookup, deterministic mathematical calculations, adaptive chart generation, and evidence-grounded insights.

#### Request Body
```json
{
  "prompt": "Compare Virat Kohli and Rohit Sharma in ODIs since 2022",
  "session_id": "optional-session-id",
  "context": {
    "conversation_id": "conv_1730000000"
  }
}
```

#### Successful Response (`200 OK`)
```json
{
  "request_id": "8fbdd63e-5efb-44ae-a030-101019f35317",
  "status": "success",
  "answer": "Comparing Virat Kohli and Rohit Sharma in ODI since 2022: Virat Kohli has accumulated 82 runs across 1 innings with a batting average of None and strike rate of 115.49. In comparison, Rohit Sharma has scored 0 runs across 0 innings with an average of N/A and strike rate of 0.0.",
  "interpretation": {
    "intent": "comparison",
    "players": ["Virat Kohli", "Rohit Sharma"],
    "format": "ODI",
    "start_date": "2022-01-01",
    "metrics": ["runs", "batting_average", "strike_rate"],
    "chart_preference": "grouped_bar",
    "confidence": 0.85
  },
  "confidence": {
    "overall_confidence": 0.88,
    "model_confidence": 0.85,
    "schema_valid": true,
    "entity_resolution_score": 1.0,
    "temporal_valid": true,
    "confidence_tier": "high",
    "explanation": "High confidence: intent and entities verified against Cricsheet database."
  },
  "provider": {
    "name": "gemini",
    "model": "gemini-2.5-flash",
    "latency_ms": 780.2,
    "fallback_used": false,
    "fallback_reason": null
  },
  "metrics": [
    {
      "player_name": "Virat Kohli",
      "total_runs": 82,
      "batting_average": null,
      "strike_rate": 115.49,
      "innings_count": 1,
      "centuries": 0,
      "fifties": 1,
      "high_score": 82,
      "high_score_not_out": true,
      "std_deviation": 0.0
    }
  ],
  "chart": {
    "chart_type": "grouped_bar",
    "title": "Player Comparison: Virat Kohli vs Rohit Sharma",
    "x_axis": { "label": "Metrics" },
    "y_axis": { "label": "Value" },
    "series": [...]
  },
  "evidence": [
    {
      "source_document": "metric_definitions.md",
      "section": "Batting Average",
      "chunk_text": "Batting average is calculated as total runs scored divided by dismissals..."
    }
  ],
  "dataset_coverage": {
    "matches": 1,
    "formats": ["ODI"]
  },
  "limitations": [
    "Dataset reflects imported Cricsheet match files, not all historical cricket."
  ],
  "clarification_required": false
}
```

#### Clarification Required Response (`200 OK`)
```json
{
  "request_id": "...",
  "status": "clarification_required",
  "answer": "Which Sharma did you mean?",
  "clarification_required": true,
  "clarification_options": ["Rohit Sharma", "Ishant Sharma"]
}
```

---

## 2. Dataset Endpoints

### `GET /api/dataset/coverage`
Returns total ingested match counts, available format breakdowns, distinct teams, date ranges, and explicit coverage limitations.

### `GET /api/dataset/status`
Returns database readiness, connection status, last ingestion timestamp, and total deliveries indexed.

---

## 3. Evaluation & Observability Endpoints

### `GET /api/evaluation/summary`
Returns the latest benchmark accuracy, entity F1-score, format accuracy, average latency, and fallback frequency.

### `POST /api/evaluation/run`
Executes the evaluation suite on-demand and updates benchmark summary telemetry.

### `GET /api/evaluation/providers`
Returns health, timeouts, circuit breaker status, and active model names for Gemini and Qwen.
