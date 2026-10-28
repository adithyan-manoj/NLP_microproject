import React from 'react';
import { TrendingUp, Target, Zap, ShieldCheck, Flame, Hash } from 'lucide-react';

export default function StatCards({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      label: "Total Runs",
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
      value: typeof stats.std_deviation === 'number' ? `±${stats.std_deviation.toFixed(1)}` : "—",
      subtext: stats.consistency_rating || "Score dispersion",
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
