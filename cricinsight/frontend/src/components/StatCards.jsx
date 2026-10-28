import React from 'react';
import { TrendingUp, Target, Zap, ShieldCheck, Flame, Hash, UserCheck } from 'lucide-react';

export default function StatCards({ stats, comparison }) {
  if (!stats) return null;

  // Multi-player Comparison Cards View
  if (comparison && comparison.length > 1) {
    return (
      <div className="flex flex-col gap-3">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Head-to-Head Comparative Overview</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {comparison.map((p, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/40 shadow-xl backdrop-blur flex flex-col justify-between gap-4 transition-transform hover:-translate-y-0.5"
            >
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div>
                  <h4 className="font-bold text-base text-white tracking-tight">{p.player_name}</h4>
                  <span className="text-[11px] text-slate-400">{p.innings_count} innings played</span>
                </div>
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold text-xs">
                  #{idx + 1}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Runs</div>
                  <div className="text-lg font-bold text-amber-400">{p.total_runs.toLocaleString()}</div>
                </div>
                <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Average</div>
                  <div className="text-lg font-bold text-emerald-400">{p.batting_average.toFixed(1)}</div>
                </div>
                <div className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Strike Rate</div>
                  <div className="text-lg font-bold text-cyan-400">{p.strike_rate.toFixed(1)}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-2.5">
                <span>100s / 50s: <strong className="text-white">{p.centuries} / {p.fifties}</strong></span>
                <span>Top: <strong className="text-white">{p.high_score}{p.high_score_not_out ? '*' : ''}</strong></span>
                <span>Consistency: <strong className="text-slate-200">±{p.std_deviation}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Single player / Match cards
  const cards = [
    {
      label: "Total Volume",
      value: stats.total_runs?.toLocaleString() ?? "—",
      subtext: `${stats.balls_faced ?? 0} balls faced`,
      icon: Flame,
      color: "from-amber-500/20 to-orange-500/10 text-amber-400 border-amber-500/30",
    },
    {
      label: "Batting Average",
      value: typeof stats.batting_average === 'number' ? stats.batting_average.toFixed(2) : (stats.batting_average ?? "—"),
      subtext: `${stats.innings_count ?? 0} innings (${stats.dismissals ?? 0} outs)`,
      icon: Target,
      color: "from-emerald-500/20 to-teal-500/10 text-emerald-400 border-emerald-500/30",
    },
    {
      label: "Strike Rate",
      value: typeof stats.strike_rate === 'number' ? stats.strike_rate.toFixed(1) : (stats.strike_rate ?? "—"),
      subtext: `Runs per 100 balls`,
      icon: Zap,
      color: "from-cyan-500/20 to-blue-500/10 text-cyan-400 border-cyan-500/30",
    },
    {
      label: "High Score",
      value: stats.high_score !== undefined ? `${stats.high_score}${stats.high_score_not_out ? '*' : ''}` : "—",
      subtext: `100s: ${stats.centuries ?? 0} | 50s: ${stats.fifties ?? 0}`,
      icon: TrendingUp,
      color: "from-purple-500/20 to-pink-500/10 text-purple-400 border-purple-500/30",
    },
    {
      label: "Consistency (Std Dev)",
      value: typeof stats.std_deviation === 'number' && stats.std_deviation > 0 ? `±${stats.std_deviation.toFixed(1)}` : (stats.consistency_rating || "Evaluated"),
      subtext: stats.std_deviation > 0 ? stats.consistency_rating : "Match evaluation",
      icon: ShieldCheck,
      color: "from-indigo-500/20 to-violet-500/10 text-indigo-400 border-indigo-500/30",
    },
    {
      label: "Boundaries",
      value: `${stats.fours ?? 0} / ${stats.sixes ?? 0}`,
      subtext: `4s / 6s (${(((stats.boundary_runs || 0) / (stats.total_runs || 1)) * 100).toFixed(0)}% boundary runs)`,
      icon: Hash,
      color: "from-rose-500/20 to-red-500/10 text-rose-400 border-rose-500/30",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
      {cards.map((c, idx) => {
        const Icon = c.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl bg-gradient-to-br ${c.color} border bg-slate-900/60 backdrop-blur flex flex-col justify-between transition-transform hover:-translate-y-0.5`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-400 truncate">{c.label}</span>
              <Icon className="w-4 h-4 opacity-80" />
            </div>
            <div>
              <div className="text-2xl font-bold tracking-tight text-white mb-1">
                {c.value}
              </div>
              <div className="text-[11px] text-slate-400 truncate">
                {c.subtext}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
