import React from 'react';
import { User, Calendar, Shield, Award, Layers } from 'lucide-react';

export default function QueryScopeBadge({ scope }) {
  if (!scope) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
      <span className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
        Resolved Scope:
      </span>

      {scope.players && scope.players.length > 0 && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 font-medium">
          <User className="w-3 h-3 text-emerald-400" />
          {scope.players.join(', ')}
        </span>
      )}

      {scope.format && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/10 border border-blue-500/20 text-blue-300 font-medium">
          <Layers className="w-3 h-3 text-blue-400" />
          {scope.format}
        </span>
      )}

      {scope.opponent && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20 text-purple-300 font-medium">
          <Shield className="w-3 h-3 text-purple-400" />
          vs {scope.opponent}
        </span>
      )}

      {scope.date_range && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 font-medium">
          <Calendar className="w-3 h-3 text-amber-400" />
          {scope.date_range}
        </span>
      )}

      {scope.analysis_type && (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-slate-300">
          <Award className="w-3 h-3 text-slate-400" />
          {scope.analysis_type}
        </span>
      )}
    </div>
  );
}
