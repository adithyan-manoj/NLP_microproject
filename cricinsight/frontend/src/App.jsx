import React, { useState, useEffect } from 'react';
import {
  Activity,
  Database,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  TrendingUp,
  Shield,
  Layers,
  History,
  RefreshCw,
} from 'lucide-react';

import { checkHealth, analyzeQuery } from './services/api';
import QueryInput from './components/QueryInput';
import QueryScopeBadge from './components/QueryScopeBadge';
import StatCards from './components/StatCards';
import ChartRenderer from './components/ChartRenderer';
import InsightPanel from './components/InsightPanel';
import SkeletonLoader from './components/SkeletonLoader';

export default function App() {
  const [health, setHealth] = useState({ status: 'checking', counts: null });
  const [isLoading, setIsLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [recentQueries, setRecentQueries] = useState([
    "How has Virat Kohli performed against Australia in ODIs?",
    "Compare Rohit Sharma and Virat Kohli in T20 internationals",
  ]);

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = () => {
    checkHealth()
      .then((data) => setHealth({ status: 'connected', data, counts: data.counts }))
      .catch((err) => setHealth({ status: 'error', error: err.message, counts: null }));
  };

  const handleSearch = async (prompt) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeQuery(prompt, analysisResult?.scope || null);
      setAnalysisResult(result);

      // Add to query history (unique, max 5)
      setRecentQueries((prev) => {
        const filtered = prev.filter((q) => q.toLowerCase() !== prompt.toLowerCase());
        return [prompt, ...filtered].slice(0, 5);
      });
    } catch (err) {
      setError(err.message || 'Failed to analyze query. Please try rephrasing.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 transition-all">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 via-teal-600 to-emerald-700 flex items-center justify-center text-xl shadow-lg shadow-emerald-950/50 ring-1 ring-emerald-400/20">
              🏏
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 via-teal-200 to-cyan-400 bg-clip-text text-transparent">
                  CricInsight
                </h1>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
                  OLAP Engine
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                NLP-Powered Cricket Performance Analysis System
              </p>
            </div>
          </div>

          {/* Backend Status Pill */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-slate-800 bg-slate-900/90 shadow-inner">
              {health.status === 'connected' ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-slate-300 font-medium hidden md:inline">
                    DuckDB Online:
                  </span>
                  <span className="text-emerald-400 font-semibold">
                    {health.counts?.matches ? `${health.counts.matches.toLocaleString()} matches` : 'Ready'}
                  </span>
                  {health.counts?.deliveries && (
                    <span className="text-slate-500 hidden lg:inline">
                      ({(health.counts.deliveries / 1000).toFixed(0)}k deliveries)
                    </span>
                  )}
                </>
              ) : health.status === 'checking' ? (
                <>
                  <Activity className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                  <span className="text-slate-400">Connecting...</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                  <span className="text-rose-300">Backend Offline</span>
                  <button
                    type="button"
                    onClick={fetchHealth}
                    className="p-1 hover:text-white transition"
                    title="Retry connection"
                  >
                    <RefreshCw className="w-3 h-3" />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 flex flex-col gap-8">
        {/* Prominent Natural Language Query Hero Section */}
        <section className="relative overflow-hidden rounded-3xl border border-slate-800/90 bg-gradient-to-b from-slate-900/90 via-slate-900/50 to-slate-950 p-6 sm:p-10 shadow-2xl backdrop-blur">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.08),transparent_50%)] pointer-events-none" />
          <div className="absolute -top-24 -left-24 w-72 h-72 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-4xl mx-auto flex flex-col gap-6 text-center sm:text-left">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-3">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>Conversational Cricket Analytics</span>
              </div>
              <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
                Ask cricket questions in plain English.
              </h2>
              <p className="text-slate-400 text-sm sm:text-base mt-2 max-w-2xl">
                Convert natural queries into parameterized DuckDB OLAP computations with instant visual charts and grounded statistical summaries.
              </p>
            </div>

            {/* Prominent Query Input */}
            <QueryInput onSearch={handleSearch} isLoading={isLoading} />
          </div>
        </section>

        {/* Dynamic Content Area */}
        {isLoading ? (
          <SkeletonLoader />
        ) : error ? (
          <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-500/30 text-rose-200 flex items-start gap-4 shadow-xl">
            <AlertCircle className="w-6 h-6 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-base text-rose-300">Analysis Error</h4>
              <p className="text-sm text-slate-300 mt-1">{error}</p>
              <button
                type="button"
                onClick={() => handleSearch(recentQueries[0])}
                className="mt-3 px-4 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/30 text-xs font-medium text-rose-200 transition"
              >
                Retry with default query
              </button>
            </div>
          </div>
        ) : analysisResult ? (
          <div className="flex flex-col gap-6">
            {/* Resolved Query Scope Badge */}
            <QueryScopeBadge scope={analysisResult.scope} />

            {/* Key Performance Indicators */}
            <StatCards stats={analysisResult.stats} />

            {/* Adaptive Chart Rendering */}
            <ChartRenderer chartSpec={analysisResult.chart} />

            {/* Evidence-Based Insight Panel */}
            <InsightPanel
              insight={analysisResult.insight}
              observations={analysisResult.observations}
            />
          </div>
        ) : (
          /* Initial Empty Dashboard State */
          <div className="flex flex-col gap-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-emerald-500/30 transition flex flex-col gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-white text-base">Ball-by-Ball Accuracy</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Queries are evaluated over 732,536 normalized deliveries stored in a local columnar DuckDB database, ensuring zero hallucinated statistics.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-cyan-500/30 transition flex flex-col gap-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-white text-base">Adaptive Visualizations</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Intelligently chooses between line progressions, comparisons, and rolling trends based on the semantic intent of your query.
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-purple-500/30 transition flex flex-col gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-white text-base">Mathematical Rigor</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Evaluates cricket scoring conventions, dismissal ratios, strike rates, standard deviation (&sigma;) for consistency, and milestone innings.
                </p>
              </div>
            </div>

            {/* Quick-Start Query Cards */}
            <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 flex flex-col gap-4">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <History className="w-4 h-4 text-emerald-400" />
                <span>Featured Analytical Explorations</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  {
                    title: "Virat Kohli vs Australia in ODIs",
                    desc: "Analyze run progression and average across head-to-head matches",
                    query: "How has Virat Kohli performed against Australia in ODIs?",
                  },
                  {
                    title: "Rohit Sharma vs Virat Kohli (T20)",
                    desc: "Compare strike rates, averages, and volume in T20 internationals",
                    query: "Compare Rohit Sharma and Virat Kohli in T20 internationals",
                  },
                  {
                    title: "David Warner against Pakistan",
                    desc: "Inspect scoring consistency and boundary conversion in ODIs",
                    query: "David Warner vs Pakistan in ODIs",
                  },
                ].map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSearch(item.query)}
                    className="p-4 rounded-xl bg-slate-900/80 hover:bg-slate-800/90 border border-slate-800 hover:border-emerald-500/40 text-left transition group flex flex-col justify-between gap-2 shadow-sm"
                  >
                    <div>
                      <div className="font-semibold text-sm text-slate-200 group-hover:text-emerald-300 transition-colors">
                        {item.title}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {item.desc}
                      </div>
                    </div>
                    <div className="text-[11px] font-medium text-emerald-400/80 flex items-center gap-1 mt-2">
                      <span>Run analysis</span> &rarr;
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Modern Minimalist Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 px-6 py-5 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>CricInsight System</span>
            <span>&bull;</span>
            <span>React (Vite) + Tailwind CSS + FastAPI + DuckDB OLAP</span>
          </div>
          <div>
            Data sourced from <a href="https://cricsheet.org" target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">Cricsheet</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
