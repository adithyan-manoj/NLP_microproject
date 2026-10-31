-- CricInsight PostgreSQL 16 + pgvector Database Schema
-- Migration 001: Initial Schema

CREATE EXTENSION IF NOT EXISTS vector;

-- Table: matches
CREATE TABLE IF NOT EXISTS matches (
    id VARCHAR(64) PRIMARY KEY,
    source VARCHAR(32) NOT NULL DEFAULT 'cricsheet',
    source_match_id VARCHAR(64) NOT NULL,
    dates TEXT[] NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    match_type VARCHAR(32) NOT NULL,
    match_type_number INT,
    competition VARCHAR(128),
    season VARCHAR(32),
    gender VARCHAR(16) DEFAULT 'male',
    venue VARCHAR(256),
    city VARCHAR(128),
    teams TEXT[] NOT NULL,
    toss_winner VARCHAR(128),
    toss_decision VARCHAR(16),
    outcome_winner VARCHAR(128),
    outcome_by_runs INT,
    outcome_by_wickets INT,
    outcome_result VARCHAR(64),
    outcome_method VARCHAR(32),
    player_of_match TEXT[],
    balls_per_over INT DEFAULT 6,
    overs_limit INT,
    source_file_hash VARCHAR(64) NOT NULL,
    source_payload JSONB,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_matches_source_match UNIQUE (source, source_match_id)
);

CREATE INDEX IF NOT EXISTS idx_matches_format ON matches(match_type);
CREATE INDEX IF NOT EXISTS idx_matches_start_date ON matches(start_date);
CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition);
CREATE INDEX IF NOT EXISTS idx_matches_venue ON matches(venue);
CREATE INDEX IF NOT EXISTS idx_matches_hash ON matches(source_file_hash);

-- Table: players
CREATE TABLE IF NOT EXISTS players (
    id VARCHAR(64) PRIMARY KEY,
    canonical_name VARCHAR(128) NOT NULL,
    cricsheet_id VARCHAR(64),
    country VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_players_canonical ON players(canonical_name);
CREATE INDEX IF NOT EXISTS idx_players_cricsheet ON players(cricsheet_id);

-- Table: player_aliases
CREATE TABLE IF NOT EXISTS player_aliases (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(64) NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    alias VARCHAR(128) NOT NULL,
    normalized_alias VARCHAR(128) NOT NULL,
    source VARCHAR(32) DEFAULT 'manual',
    is_primary BOOLEAN DEFAULT FALSE,
    CONSTRAINT uq_player_alias UNIQUE (player_id, normalized_alias)
);

CREATE INDEX IF NOT EXISTS idx_player_aliases_norm ON player_aliases(normalized_alias);

-- Table: innings
CREATE TABLE IF NOT EXISTS innings (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(64) NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    innings_number INT NOT NULL,
    batting_team VARCHAR(128) NOT NULL,
    bowling_team VARCHAR(128) NOT NULL,
    declared BOOLEAN DEFAULT FALSE,
    overs_limit INT,
    total_runs INT DEFAULT 0,
    total_wickets INT DEFAULT 0,
    total_legal_balls INT DEFAULT 0,
    CONSTRAINT uq_innings_match_num UNIQUE (match_id, innings_number)
);

CREATE INDEX IF NOT EXISTS idx_innings_match ON innings(match_id);

-- Table: deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    id BIGSERIAL PRIMARY KEY,
    innings_id INT NOT NULL REFERENCES innings(id) ON DELETE CASCADE,
    match_id VARCHAR(64) NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    over_num INT NOT NULL,
    ball_num INT NOT NULL,
    delivery_index INT NOT NULL,
    batter_id VARCHAR(64),
    batter_name VARCHAR(128) NOT NULL,
    bowler_id VARCHAR(64),
    bowler_name VARCHAR(128) NOT NULL,
    non_striker_id VARCHAR(64),
    non_striker_name VARCHAR(128) NOT NULL,
    batter_runs INT NOT NULL DEFAULT 0,
    extra_runs INT NOT NULL DEFAULT 0,
    total_runs INT NOT NULL DEFAULT 0,
    is_wide BOOLEAN NOT NULL DEFAULT FALSE,
    is_noball BOOLEAN NOT NULL DEFAULT FALSE,
    is_bye BOOLEAN NOT NULL DEFAULT FALSE,
    is_legbye BOOLEAN NOT NULL DEFAULT FALSE,
    is_penalty BOOLEAN NOT NULL DEFAULT FALSE,
    is_legal_ball BOOLEAN NOT NULL DEFAULT TRUE,
    is_ball_faced BOOLEAN NOT NULL DEFAULT TRUE,
    bowler_conceded_runs INT NOT NULL DEFAULT 0,
    is_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    dismissal_kind VARCHAR(64),
    player_dismissed VARCHAR(128),
    bowler_credited_wicket BOOLEAN NOT NULL DEFAULT FALSE,
    extras_detail JSONB,
    wicket_detail JSONB
);

CREATE INDEX IF NOT EXISTS idx_deliveries_match ON deliveries(match_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_innings ON deliveries(innings_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_batter ON deliveries(batter_name);
CREATE INDEX IF NOT EXISTS idx_deliveries_bowler ON deliveries(bowler_name);
CREATE INDEX IF NOT EXISTS idx_deliveries_match_batter ON deliveries(match_id, batter_name);
CREATE INDEX IF NOT EXISTS idx_deliveries_match_bowler ON deliveries(match_id, bowler_name);

-- Table: knowledge_chunks (Hybrid RAG)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source_document VARCHAR(128) NOT NULL,
    section VARCHAR(128) NOT NULL,
    title VARCHAR(256),
    chunk_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(768),
    tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_tsv ON knowledge_chunks USING GIN(tsv);
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_chunks(source_document);

-- Table: ingestion_runs
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(64) NOT NULL DEFAULT 'cricsheet',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    files_processed INT DEFAULT 0,
    inserted_count INT DEFAULT 0,
    updated_count INT DEFAULT 0,
    skipped_count INT DEFAULT 0,
    rejected_count INT DEFAULT 0,
    error_details JSONB DEFAULT '[]'::jsonb
);

-- Table: query_logs & nlp_predictions
CREATE TABLE IF NOT EXISTS query_logs (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    session_id VARCHAR(64),
    provider VARCHAR(32),
    model_name VARCHAR(64),
    status VARCHAR(32) NOT NULL,
    latency_ms FLOAT,
    fallback_used BOOLEAN DEFAULT FALSE,
    fallback_reason VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS nlp_predictions (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) REFERENCES query_logs(request_id) ON DELETE CASCADE,
    raw_response TEXT,
    validated_schema JSONB,
    predicted_intent VARCHAR(64),
    confidence_score FLOAT,
    schema_valid BOOLEAN,
    entity_resolution_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: benchmark_questions & evaluation_runs
CREATE TABLE IF NOT EXISTS benchmark_questions (
    id SERIAL PRIMARY KEY,
    question_id VARCHAR(32) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    category VARCHAR(64) NOT NULL,
    expected_intent VARCHAR(64) NOT NULL,
    expected_players TEXT[],
    expected_opponent VARCHAR(64),
    expected_format VARCHAR(32),
    expected_metrics TEXT[],
    expected_start_date DATE,
    expected_recent_n INT,
    expected_chart_preference VARCHAR(32),
    should_clarify BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    provider VARCHAR(32) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    total_questions INT NOT NULL,
    intent_accuracy FLOAT NOT NULL,
    entity_precision FLOAT NOT NULL,
    entity_recall FLOAT NOT NULL,
    entity_f1 FLOAT NOT NULL,
    exact_match_rate FLOAT NOT NULL,
    schema_valid_rate FLOAT NOT NULL,
    avg_latency_ms FLOAT NOT NULL,
    fallback_rate FLOAT NOT NULL,
    summary_report JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS benchmark_results (
    id SERIAL PRIMARY KEY,
    evaluation_run_id INT REFERENCES evaluation_runs(id) ON DELETE CASCADE,
    question_id VARCHAR(32) REFERENCES benchmark_questions(question_id),
    passed BOOLEAN NOT NULL,
    predicted_intent VARCHAR(64),
    predicted_players TEXT[],
    intent_match BOOLEAN NOT NULL,
    entity_match BOOLEAN NOT NULL,
    exact_match BOOLEAN NOT NULL,
    latency_ms FLOAT NOT NULL,
    raw_prediction JSONB
);
