import React from 'react';
import {
  TrendingUp,
  Target,
  Zap,
  ShieldCheck,
  Flame,
  Award,
  Layers,
  BarChart2,
  Calendar,
  Sparkles,
  Crown,
} from 'lucide-react';

/**
 * StatCards — Precision Cricket Performance Scorecard
 * 
 * Follows Frontend Specialist & Sports Analytics Standards:
 * - Tabular numerals (font-mono) for numbers to prevent visual jitter
 * - Cohesive professional dark-mode palette (no arbitrary rainbow gradients)
 * - Clear statistical hierarchy: Primary Impact -> Milestones & Boundaries -> Workload & Consistency
 * - Head-to-Head comparative mode with leader metrics
 */
export default function StatCards({ stats, comparison, metrics }) {
  const effectiveComparison = comparison || (Array.isArray(metrics) && metrics.length > 1 ? metrics : null);
  const effectiveStats = stats || (Array.isArray(metrics) && metrics.length === 1 ? metrics[0] : (!effectiveComparison && metrics ? metrics : null));

  if (!effectiveStats && !effectiveComparison) return null;

  // --------------------------------------------------------------------------
  // 1. MULTI-PLAYER HEAD-TO-HEAD COMPARATIVE VIEW
  // --------------------------------------------------------------------------
  if (effectiveComparison && effectiveComparison.length > 1) {
    // Determine leader for key categories
    const maxRuns = Math.max(...effectiveComparison.map(p => p.total_runs || p.runs || 0));
    const maxAvg = Math.max(...effectiveComparison.map(p => p.batting_average || p.average || 0));
    const maxSR = Math.max(...effectiveComparison.map(p => p.strike_rate || 0));

    return (
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Head-to-Head Comparative Breakdown</span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            {effectiveComparison.length} Players Analyzed
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {effectiveComparison.map((p, idx) => {
            const pRuns = p.total_runs ?? p.runs ?? 0;
            const pAvg = typeof p.batting_average === 'number' ? p.batting_average : (typeof p.average === 'number' ? p.average : 0);
            const pSR = p.strike_rate ?? 0;
            const isRunLeader = pRuns === maxRuns && maxRuns > 0;
            const isAvgLeader = pAvg === maxAvg && maxAvg > 0;
            const isSRLeader = pSR === maxSR && maxSR > 0;

            return (
              <div
                key={idx}
                className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/30 transition-all flex flex-col justify-between gap-4"
              >
                {/* Player Header */}
                <div className="flex items-start justify-between border-b border-slate-800/80 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-base text-white tracking-tight">
                        {p.player_name || p.player || `Player ${idx + 1}`}
                      </h4>
                      {isRunLeader && (
                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
                          <Crown className="w-3 h-3 text-amber-400" /> Top Scorer
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {p.matches ? `${p.matches} matches • ` : ''}{p.innings_count ?? p.innings ?? 0} innings
                    </span>
                  </div>
                  <div className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-mono text-xs font-bold border border-slate-700">
                    #{idx + 1}
                  </div>
                </div>

                {/* Core Three Pillars */}
                <div className="grid grid-cols-3 gap-2">
                  <div className={`p-3 rounded-xl border text-center transition ${isRunLeader ? 'bg-amber-950/20 border-amber-500/30' : 'bg-slate-950/60 border-slate-800/80'}`}>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Runs</div>
                    <div className="text-xl font-bold font-mono text-white mt-0.5">
                      {pRuns.toLocaleString()}
                    </div>
                    {isRunLeader && <span className="text-[9px] text-amber-400 font-bold block">LEADER</span>}
                  </div>

                  <div className={`p-3 rounded-xl border text-center transition ${isAvgLeader ? 'bg-emerald-950/20 border-emerald-500/30' : 'bg-slate-950/60 border-slate-800/80'}`}>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Average</div>
                    <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
                      {pAvg ? pAvg.toFixed(2) : '—'}
                    </div>
                    {isAvgLeader && <span className="text-[9px] text-emerald-400 font-bold block">LEADER</span>}
                  </div>

                  <div className={`p-3 rounded-xl border text-center transition ${isSRLeader ? 'bg-cyan-950/20 border-cyan-500/30' : 'bg-slate-950/60 border-slate-800/80'}`}>
                    <div className="text-[10px] uppercase font-bold text-slate-400">Strike Rate</div>
                    <div className="text-xl font-bold font-mono text-cyan-400 mt-0.5">
                      {pSR ? pSR.toFixed(1) : '—'}
                    </div>
                    {isSRLeader && <span className="text-[9px] text-cyan-400 font-bold block">LEADER</span>}
                  </div>
                </div>

                {/* Sub-Metrics Row */}
                <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2.5 font-mono">
                  <span>100s/50s: <strong className="text-white">{p.centuries ?? p.hundreds ?? 0}/{p.fifties ?? 0}</strong></span>
                  <span>HS: <strong className="text-white">{p.high_score ?? '—'}{p.high_score_not_out ? '*' : ''}</strong></span>
                  <span>4s/6s: <strong className="text-slate-300">{p.fours ?? 0}/{p.sixes ?? 0}</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // 2. SINGLE PLAYER / MATCH PRECISION KPI DECK
  // --------------------------------------------------------------------------
  const target = effectiveStats || {};
  const runs = target.total_runs ?? target.runs ?? 0;
  const innings = target.innings_count ?? target.innings ?? 0;
  const matches = target.matches ?? innings;
  const balls = target.balls_faced ?? 0;
  const notOuts = target.not_outs ?? (target.dismissals !== undefined ? innings - target.dismissals : 0);
  const avg = typeof target.batting_average === 'number' ? target.batting_average.toFixed(2) : (target.batting_average ?? (typeof target.average === 'number' ? target.average.toFixed(2) : '—'));
  const sr = typeof target.strike_rate === 'number' ? target.strike_rate.toFixed(1) : (target.strike_rate ?? '—');
  const hs = target.high_score !== undefined ? `${target.high_score}${target.high_score_not_out ? '*' : ''}` : '—';
  const hundreds = target.centuries ?? target.hundreds ?? 0;
  const fifties = target.fifties ?? 0;
  const fours = target.fours ?? 0;
  const sixes = target.sixes ?? 0;
  const boundaryRuns = target.boundary_runs ?? (fours * 4 + sixes * 6);
  const boundaryPct = runs > 0 ? ((boundaryRuns / runs) * 100).toFixed(1) : '0.0';
  const consistency = target.std_deviation > 0 ? `±${target.std_deviation.toFixed(1)}` : (target.consistency_rating || 'Evaluated');

  return (
    <div className="flex flex-col gap-3">
      {/* Primary 4-Pillar Scorecard Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {/* Metric 1: Total Runs */}
        <div className="p-4 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800 hover:border-amber-500/40 transition-all shadow-lg flex flex-col justify-between group">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Total Runs</span>
            <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 group-hover:scale-110 transition">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <span className="text-3xl font-extrabold text-white font-mono tracking-tight">
              {runs.toLocaleString()}
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full" style={{ width: '85%' }} />
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              Across {innings} innings ({balls ? `${balls} balls` : 'all fixtures'})
            </div>
          </div>
        </div>

        {/* Metric 2: Batting Average */}
        <div className="p-4 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800 hover:border-emerald-500/40 transition-all shadow-lg flex flex-col justify-between group">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Batting Average</span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 group-hover:scale-110 transition">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <span className="text-3xl font-extrabold text-emerald-400 font-mono tracking-tight">
              {avg}
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full" style={{ width: `${Math.min(100, (parseFloat(avg) || 0) * 1.5)}%` }} />
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              {notOuts > 0 ? `${notOuts} not-out innings` : 'Standard dismissals'}
            </div>
          </div>
        </div>

        {/* Metric 3: Strike Rate */}
        <div className="p-4 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800 hover:border-cyan-500/40 transition-all shadow-lg flex flex-col justify-between group">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Strike Rate</span>
            <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 group-hover:scale-110 transition">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <span className="text-3xl font-extrabold text-cyan-400 font-mono tracking-tight">
              {sr}
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full" style={{ width: `${Math.min(100, ((parseFloat(sr) || 0) / 180) * 100)}%` }} />
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              Runs scored per 100 balls
            </div>
          </div>
        </div>

        {/* Metric 4: High Score & Milestones */}
        <div className="p-4 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800 hover:border-purple-500/40 transition-all shadow-lg flex flex-col justify-between group">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Highest Score</span>
            <div className="p-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 group-hover:scale-110 transition">
              <Award className="w-4 h-4" />
            </div>
          </div>
          <div className="my-2">
            <span className="text-3xl font-extrabold text-purple-400 font-mono tracking-tight">
              {hs}
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full" style={{ width: '90%' }} />
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              100s: <strong className="text-white">{hundreds}</strong> &bull; 50s: <strong className="text-white">{fifties}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Detailed Cricket Breakdown Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-slate-700 transition flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Matches / Innings</span>
            <span className="text-sm font-bold text-slate-200 font-mono">{matches} / {innings}</span>
          </div>
          <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400">
            <Calendar className="w-3.5 h-3.5" />
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-amber-500/30 transition flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Boundaries (4s / 6s)</span>
            <span className="text-sm font-bold text-amber-300 font-mono">{fours} fours &bull; {sixes} sixes</span>
          </div>
          <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <TrendingUp className="w-3.5 h-3.5" />
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-cyan-500/30 transition flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Boundary Share</span>
            <span className="text-sm font-bold text-slate-200 font-mono">{boundaryPct}% of runs</span>
          </div>
          <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <BarChart2 className="w-3.5 h-3.5" />
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/90 hover:border-emerald-500/30 transition flex items-center justify-between">
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Consistency Index</span>
            <span className="text-sm font-bold text-emerald-300 font-mono">{consistency}</span>
          </div>
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>
    </div>
  );
}
