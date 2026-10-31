import React, { useState, useEffect } from 'react';
import {
  Users,
  TrendingUp,
  Sparkles,
  BarChart2,
  ArrowRightLeft,
  Shield,
  Award,
  Search,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

import { sendChatQuery } from '../services/api';

export default function PlayerComparisonStudio({ onSelectQuery }) {
  const [player1, setPlayer1] = useState('Virat Kohli');
  const [player2, setPlayer2] = useState('Rohit Sharma');
  const [format, setFormat] = useState('T20');
  const [isLoading, setIsLoading] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    handleRunComparison();
  }, []);

  const handleRunComparison = async () => {
    if (!player1.trim() || !player2.trim()) return;
    setIsLoading(true);
    setError(null);

    const prompt = `Compare ${player1} and ${player2} in ${format}`;
    try {
      const res = await sendChatQuery(prompt);
      setComparisonData(res);
    } catch (err) {
      setError(err.message || 'Failed to compare players.');
    } finally {
      setIsLoading(false);
    }
  };

  const metrics = comparisonData?.metrics || [];
  const p1Metrics = metrics[0] || null;
  const p2Metrics = metrics[1] || null;

  // Build chart dataset
  const chartData = [
    {
      metric: 'Runs',
      [p1Metrics?.player_name || player1]: p1Metrics?.total_runs || 0,
      [p2Metrics?.player_name || player2]: p2Metrics?.total_runs || 0,
    },
    {
      metric: 'Average',
      [p1Metrics?.player_name || player1]: p1Metrics?.batting_average || 0,
      [p2Metrics?.player_name || player2]: p2Metrics?.batting_average || 0,
    },
    {
      metric: 'Strike Rate',
      [p1Metrics?.player_name || player1]: p1Metrics?.strike_rate || 0,
      [p2Metrics?.player_name || player2]: p2Metrics?.strike_rate || 0,
    },
    {
      metric: 'Boundaries (4s)',
      [p1Metrics?.player_name || player1]: p1Metrics?.fours || 0,
      [p2Metrics?.player_name || player2]: p2Metrics?.fours || 0,
    },
    {
      metric: 'Maximums (6s)',
      [p1Metrics?.player_name || player1]: p1Metrics?.sixes || 0,
      [p2Metrics?.player_name || player2]: p2Metrics?.sixes || 0,
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Header & Controls */}
      <div className="p-6 rounded-3xl cricops-card cricops-card-glow shadow-xl backdrop-blur flex flex-col md:flex-row items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold">
              ⚡
            </span>
            <h2 className="text-xl font-bold text-white tracking-tight">CricOps Comparison Studio</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic side-by-side batting & bowling evaluation across international formats.
          </p>
        </div>

        {/* Inputs */}
        <div className="flex items-center gap-2 flex-wrap w-full md:w-auto">
          <input
            type="text"
            placeholder="Player 1"
            value={player1}
            onChange={(e) => setPlayer1(e.target.value)}
            className="px-3.5 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 w-36 transition"
          />
          <span className="text-xs font-bold text-cyan-400 font-mono">VS</span>
          <input
            type="text"
            placeholder="Player 2"
            value={player2}
            onChange={(e) => setPlayer2(e.target.value)}
            className="px-3.5 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-white focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 w-36 transition"
          />

          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20 transition"
          >
            <option value="T20">T20 / IPL</option>
            <option value="ODI">ODI</option>
            <option value="Test">Test</option>
          </select>

          <button
            type="button"
            disabled={isLoading}
            onClick={handleRunComparison}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-400 to-teal-400 hover:from-cyan-300 hover:to-teal-300 text-slate-950 font-bold text-xs transition shadow-md shadow-cyan-950 disabled:opacity-50"
          >
            {isLoading ? 'Comparing...' : 'Compare'}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/20 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Side-by-Side Stat Cards */}
      {metrics.length >= 2 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Player 1 Card */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-cyan-500/30 flex flex-col gap-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-extrabold text-white text-lg tracking-tight">
                  {p1Metrics.player_name}
                </h3>
                <span className="text-xs text-cyan-400 font-mono">
                  {p1Metrics.matches || 0} Matches • {p1Metrics.innings || 0} Innings
                </span>
              </div>
              <span className="w-4 h-4 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400" />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Runs</span>
                <p className="text-xl font-bold font-mono text-white mt-0.5">{p1Metrics.total_runs}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Average</span>
                <p className="text-xl font-bold font-mono text-cyan-300 mt-0.5">{p1Metrics.batting_average}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Strike Rate</span>
                <p className="text-xl font-bold font-mono text-emerald-400 mt-0.5">{p1Metrics.strike_rate}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
                <span className="text-slate-500">100s / 50s</span>
                <p className="font-bold text-slate-200 mt-0.5">{p1Metrics.centuries || 0} / {p1Metrics.half_centuries || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
                <span className="text-slate-500">Fours (4s)</span>
                <p className="font-bold text-slate-200 mt-0.5">{p1Metrics.fours || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
                <span className="text-slate-500">Sixes (6s)</span>
                <p className="font-bold text-slate-200 mt-0.5">{p1Metrics.sixes || 0}</p>
              </div>
            </div>
          </div>

          {/* Player 2 Card */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-emerald-500/30 flex flex-col gap-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-extrabold text-white text-lg tracking-tight">
                  {p2Metrics.player_name}
                </h3>
                <span className="text-xs text-emerald-400 font-mono">
                  {p2Metrics.matches || 0} Matches • {p2Metrics.innings || 0} Innings
                </span>
              </div>
              <span className="w-4 h-4 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400" />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Runs</span>
                <p className="text-xl font-bold font-mono text-white mt-0.5">{p2Metrics.total_runs}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Average</span>
                <p className="text-xl font-bold font-mono text-emerald-300 mt-0.5">{p2Metrics.batting_average}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Strike Rate</span>
                <p className="text-xl font-bold font-mono text-cyan-400 mt-0.5">{p2Metrics.strike_rate}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
                <span className="text-slate-500">100s / 50s</span>
                <p className="font-bold text-slate-200 mt-0.5">{p2Metrics.centuries || 0} / {p2Metrics.half_centuries || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
                <span className="text-slate-500">Fours (4s)</span>
                <p className="font-bold text-slate-200 mt-0.5">{p2Metrics.fours || 0}</p>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center">
                <span className="text-slate-500">Sixes (6s)</span>
                <p className="font-bold text-slate-200 mt-0.5">{p2Metrics.sixes || 0}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Comparative Grouped Bar Chart */}
      <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 flex flex-col gap-4 shadow-xl">
        <h3 className="font-bold text-white text-base">Key Metrics Comparison Chart</h3>
        <div className="w-full h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="metric" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '12px',
                  color: '#f8fafc',
                }}
              />
              <Legend />
              <Bar dataKey={p1Metrics?.player_name || player1} fill="#06b6d4" radius={[6, 6, 0, 0]} />
              <Bar dataKey={p2Metrics?.player_name || player2} fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grounded Insight Narrative */}
      {comparisonData?.answer && (
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 text-slate-300 text-sm leading-relaxed">
          <span className="font-bold text-white text-base block mb-2">Analysis Breakdown:</span>
          {comparisonData.answer}
        </div>
      )}
    </div>
  );
}
