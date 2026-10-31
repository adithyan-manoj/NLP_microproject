const API_BASE = '/api';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function sendChatQuery(prompt, context = null) {
  const res = await fetch(`${API_BASE}/chat/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, context }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed: ${res.statusText}`);
  }
  return res.json();
}

export async function analyzeQuery(prompt, context = null) {
  return sendChatQuery(prompt, context);
}

export async function getDatasetCoverage() {
  const res = await fetch(`${API_BASE}/dataset/coverage`);
  if (!res.ok) throw new Error('Failed to fetch dataset coverage');
  return res.json();
}

export async function getDatasetStatus() {
  const res = await fetch(`${API_BASE}/dataset/status`);
  if (!res.ok) throw new Error('Failed to fetch dataset status');
  return res.json();
}

export async function getEvaluationSummary() {
  const res = await fetch(`${API_BASE}/evaluation/summary`);
  if (!res.ok) throw new Error('Failed to fetch evaluation summary');
  return res.json();
}

export async function getEvaluationProviders() {
  const res = await fetch(`${API_BASE}/evaluation/providers`);
  if (!res.ok) throw new Error('Failed to fetch provider status');
  return res.json();
}

export async function getEvaluationQueries(limit = 25) {
  const res = await fetch(`${API_BASE}/evaluation/queries?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch evaluation queries');
  return res.json();
}

export async function runEvaluationBenchmark() {
  const res = await fetch(`${API_BASE}/evaluation/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to execute evaluation benchmark');
  return res.json();
}

export async function getPlayers(query = '') {
  const url = query ? `${API_BASE}/players?q=${encodeURIComponent(query)}` : `${API_BASE}/players`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch players: ${res.statusText}`);
  }
  return res.json();
}

export async function getTournaments() {
  const res = await fetch(`${API_BASE}/tournaments`);
  if (!res.ok) throw new Error('Failed to fetch tournaments');
  return res.json();
}

export async function createTournament(data) {
  const res = await fetch(`${API_BASE}/tournaments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create tournament');
  return res.json();
}

export async function getTournamentDetails(tournamentId) {
  const res = await fetch(`${API_BASE}/tournaments/${tournamentId}`);
  if (!res.ok) throw new Error('Failed to fetch tournament details');
  return res.json();
}

export async function addTournamentTeam(tournamentId, data) {
  const res = await fetch(`${API_BASE}/tournaments/${tournamentId}/teams`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to add team');
  return res.json();
}

export async function createTournamentMatch(tournamentId, data) {
  const res = await fetch(`${API_BASE}/tournaments/${tournamentId}/matches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create match fixture');
  return res.json();
}

export async function recordMatchScorecard(matchId, data) {
  const res = await fetch(`${API_BASE}/tournaments/matches/${matchId}/scorecard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to record scorecard');
  return res.json();
}

export async function recordLiveBall(matchId, data) {
  const res = await fetch(`${API_BASE}/tournaments/matches/${matchId}/ball`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to log delivery');
  return res.json();
}

export async function getTournamentStandings(tournamentId) {
  const res = await fetch(`${API_BASE}/tournaments/${tournamentId}/standings`);
  if (!res.ok) throw new Error('Failed to fetch standings');
  return res.json();
}

export async function getTournamentLeaderboard(tournamentId) {
  const res = await fetch(`${API_BASE}/tournaments/${tournamentId}/leaderboard`);
  if (!res.ok) throw new Error('Failed to fetch leaderboards');
  return res.json();
}
