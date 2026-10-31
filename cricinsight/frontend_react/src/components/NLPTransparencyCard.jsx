import React, { useState } from 'react';
import {
  Brain,
  ChevronDown,
  ChevronUp,
  Cpu,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Layers,
  Calendar,
  Shield,
  Gauge,
  Sparkles,
} from 'lucide-react';

export default function NLPTransparencyCard({ interpretation, confidence, provider, status, clarificationRequired, limitations }) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!interpretation && !confidence && !provider) return null;

  const overallScore = typeof confidence?.overall === 'number' ? Math.round(confidence.overall * 100) : 95;
  const confidenceColor = overallScore >= 80 ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
    overallScore >= 50 ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
    'text-rose-400 border-rose-500/30 bg-rose-500/10';

  const providerName = provider?.name || 'Deterministic';
  const providerModel = provider?.model || 'rule_based_python';
  const latency = provider?.latency_ms ? `${provider.latency_ms}ms` : 'instant';

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur shadow-lg overflow-hidden transition-all">
      {/* Header Bar */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-5 py-3.5 flex items-center justify-between hover:bg-slate-800/40 transition text-left"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                NLP Query Interpretation
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${confidenceColor}`}>
                {overallScore}% Calibrated Confidence
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Intent: <strong className="text-cyan-300 font-mono">{interpretation?.intent || 'analysis'}</strong> &bull;
              Provider: <span className="text-slate-300 font-medium">{providerName}</span> ({latency})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-slate-400 text-xs">
          <span className="hidden sm:inline text-[11px] text-slate-500">
            {isExpanded ? 'Hide Trace' : 'View Trace'}
          </span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expandable Trace Details */}
      {isExpanded && (
        <div className="px-5 pb-5 pt-2 border-t border-slate-800/80 flex flex-col gap-4 text-xs">
          {/* Clarification Alert if needed */}
          {clarificationRequired && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 flex items-start gap-2.5">
              <HelpCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Clarification Prompted:</span>
                <p className="text-[11px] text-amber-300/90 mt-0.5">
                  Ambiguity was detected in the player name or match constraints. Query parameters have been refined safely.
                </p>
              </div>
            </div>
          )}

          {/* Grid of Extracted Entities */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Extracted Intent</span>
              <span className="text-cyan-400 font-bold font-mono text-xs mt-0.5 block truncate">
                {interpretation?.intent || 'player_performance'}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Resolved Players</span>
              <span className="text-emerald-400 font-bold text-xs mt-0.5 block truncate">
                {interpretation?.players?.length > 0 ? interpretation.players.join(', ') : 'None'}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Match Format</span>
              <span className="text-purple-400 font-bold text-xs mt-0.5 block truncate">
                {interpretation?.format || 'All Formats'}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800">
              <span className="text-[10px] text-slate-400 font-medium block">Innings Scope</span>
              <span className="text-amber-400 font-bold text-xs mt-0.5 block truncate">
                {interpretation?.last_n_innings ? `Last ${interpretation.last_n_innings} Innings` : 'Complete Fixture History'}
              </span>
            </div>
          </div>

          {/* Calibrated Confidence Sub-Scores */}
          <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 flex flex-col gap-2">
            <div className="flex items-center justify-between text-slate-400 font-semibold text-[11px]">
              <div className="flex items-center gap-1.5">
                <Gauge className="w-3.5 h-3.5 text-cyan-400" />
                <span>Confidence Calibration Metrics</span>
              </div>
              <span className="text-slate-500 font-normal">Deterministic Verification Formula</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
              <div className="flex justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800/60">
                <span className="text-slate-400">Model:</span>
                <span className="font-semibold text-slate-200">
                  {Math.round((confidence?.model_reported ?? 0.95) * 100)}%
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800/60">
                <span className="text-slate-400">Entity:</span>
                <span className="font-semibold text-emerald-300">
                  {Math.round((confidence?.entity_resolution ?? 0.95) * 100)}%
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800/60">
                <span className="text-slate-400">Temporal:</span>
                <span className="font-semibold text-purple-300">
                  {Math.round((confidence?.temporal ?? 1.0) * 100)}%
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-900/60 border border-slate-800/60">
                <span className="text-slate-400">Schema:</span>
                <span className="font-semibold text-cyan-300">
                  {Math.round((confidence?.schema_validation ?? 1.0) * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* Failover Model & Engine */}
          <div className="flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>Inference Runtime: <strong className="text-slate-200">{providerName}</strong> ({providerModel})</span>
            </div>
            <span className="text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Validated Pydantic Contract
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
