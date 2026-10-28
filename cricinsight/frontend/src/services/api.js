const API_BASE = '/api';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function analyzeQuery(prompt, context = null) {
  const res = await fetch(`${API_BASE}/analyze`, {
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

export async function getPlayers(query = '') {
  const url = query ? `${API_BASE}/players?q=${encodeURIComponent(query)}` : `${API_BASE}/players`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch players: ${res.statusText}`);
  }
  return res.json();
}
