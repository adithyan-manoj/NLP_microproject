import React from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, TrendingUp, HelpCircle } from 'lucide-react';

export default function InsightPanel({ insight, observations }) {
  if (!insight && (!observations || observations.length === 0)) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-emerald-950/20 border border-emerald-500/20 rounded-2xl p-6 shadow-xl backdrop-blur flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
          <Sparkles className="w-4 h-4" />
          <span>Evidence-Based Analytical Insight</span>
        </div>
        <span className="text-[11px] text-slate-500 font-medium bg-slate-900 px-2 py-0.5 rounded-full border border-slate-800">
          Strictly Grounded
        </span>
      </div>

      {insight && (
        <p className="text-sm md:text-base text-slate-200 leading-relaxed font-normal">
          {insight}
        </p>
      )}

      {observations && observations.length > 0 && (
        <div className="mt-1 flex flex-col gap-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Key Observations:
          </span>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {observations.map((obs, idx) => {
              const text = typeof obs === 'string'
                ? obs
                : (obs?.chunk_text || obs?.observation || obs?.text || obs?.content || (obs ? JSON.stringify(obs) : ''));
              const sourceDoc = typeof obs === 'object' && obs?.source_document ? obs.source_document : null;
              const section = typeof obs === 'object' && obs?.section ? obs.section : null;

              return (
                <li
                  key={idx}
                  className="flex flex-col gap-1.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-slate-300"
                >
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                    <span className="leading-relaxed">{text}</span>
                  </div>
                  {(sourceDoc || section) && (
                    <div className="flex items-center gap-2 pl-5 text-[10px] text-slate-500 font-mono">
                      <span>Source: <strong className="text-slate-400">{sourceDoc || 'RAG Knowledge'}</strong></span>
                      {section && <span>&bull; Section: {section}</span>}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
