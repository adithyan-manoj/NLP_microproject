import React from 'react';

export default function SkeletonLoader() {
  return (
    <div className="w-full flex flex-col gap-6 animate-pulse">
      {/* Scope badge placeholder */}
      <div className="h-10 bg-slate-900/60 rounded-xl border border-slate-800 w-1/3" />

      {/* Metric cards grid placeholder */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-24 bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
            <div className="h-3 bg-slate-800 rounded w-1/2" />
            <div className="h-6 bg-slate-800 rounded w-3/4" />
          </div>
        ))}
      </div>

      {/* Chart placeholder */}
      <div className="h-80 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
        <div className="h-5 bg-slate-800 rounded w-1/4" />
        <div className="h-48 bg-slate-800/40 rounded-xl" />
        <div className="h-3 bg-slate-800 rounded w-1/3" />
      </div>

      {/* Insight placeholder */}
      <div className="h-32 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col gap-3">
        <div className="h-4 bg-slate-800 rounded w-1/5" />
        <div className="h-4 bg-slate-800 rounded w-full" />
        <div className="h-4 bg-slate-800 rounded w-4/5" />
      </div>
    </div>
  );
}
