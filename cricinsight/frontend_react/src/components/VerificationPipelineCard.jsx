import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  Database,
  ChevronDown,
  ChevronUp,
  Layers,
  Cpu,
  Globe,
  FileCheck2,
  Sparkles,
} from 'lucide-react';

/**
 * VerificationPipelineCard renders the independent analytics & parallel external verification audit.
 * 
 * Follows User Architectural Mandates:
 * 1. Independent Local Computation (Deterministic DuckDB engine)
 * 2. Parallel Gemini Verification (Authoritative external sources)
 * 3. Field-Level Comparison (12 metrics evaluated side-by-side)
 * 4. Actual Processing States: Local computation, External verification,
 *    Discrepancy detected (only if occurred), Dataset enrichment (only if occurred),
 *    Verification completed.
 */
export default function VerificationPipelineCard({ audit }) {
  const [isTableExpanded, setIsTableExpanded] = useState(false);

  if (!audit || !audit.local_computation) return null;

  const {
    local_computation: localComp,
    external_verification: extVerif,
    discrepancy_report: discRep,
    verified_result: verResult,
    pipeline_latency_ms: latencyMs,
  } = audit;

  // Determine which processing states actually occurred
  const states = [];

  // State 1: Local computation
  states.push({
    id: 'local_computation',
    label: 'Local Computation',
    detail: `${localComp.matches_count} matches (${localComp.granularity})`,
    icon: Database,
    status: 'completed',
    color: 'emerald',
  });

  // State 2: External verification
  if (extVerif && extVerif.retrieval_status !== 'disabled') {
    states.push({
      id: 'external_verification',
      label: 'External Verification',
      detail: extVerif.source_name || 'ESPNcricinfo / Official Archives',
      icon: Globe,
      status: extVerif.retrieval_status === 'failed' ? 'failed' : 'completed',
      color: extVerif.retrieval_status === 'failed' ? 'rose' : 'cyan',
    });
  }

  // State 3: Discrepancy detected (ONLY shown if a discrepancy actually occurred)
  const hasDiscrepancy = discRep && (discRep.has_discrepancy || discRep.discrepant_fields > 0);
  if (hasDiscrepancy) {
    states.push({
      id: 'discrepancy_detected',
      label: 'Discrepancy Detected',
      detail: `${discRep.discrepant_fields} field(s) diverged`,
      icon: AlertTriangle,
      status: 'warning',
      color: 'amber',
    });
  }

  // State 4: Dataset enrichment (ONLY shown if scorecards were ingested / recalculated)
  const isEnriched = verResult?.verification_status === 'ENRICHED_AND_RECALCULATED' ||
    (discRep?.audit_trail?.some(t => t.includes('Ingested') || t.includes('enriched')));
  if (isEnriched) {
    states.push({
      id: 'dataset_enrichment',
      label: 'Dataset Enrichment',
      detail: 'Scorecards ingested & recalculated',
      icon: RefreshCw,
      status: 'completed',
      color: 'purple',
    });
  }

  // State 5: Verification completed
  if (verResult) {
    states.push({
      id: 'verification_completed',
      label: 'Verification Completed',
      detail: verResult.verification_status.replace(/_/g, ' '),
      icon: CheckCircle2,
      status: 'completed',
      color: 'emerald',
    });
  }

  // Format metric key for presentation
  const formatMetricName = (key) => {
    const names = {
      matches: 'Matches',
      innings: 'Innings',
      runs: 'Total Runs',
      balls_faced: 'Balls Faced',
      not_outs: 'Not Outs',
      batting_average: 'Batting Average',
      strike_rate: 'Strike Rate',
      high_score: 'Highest Score',
      fifties: 'Fifties (50s)',
      hundreds: 'Hundreds (100s)',
      fours: 'Boundaries (4s)',
      sixes: 'Sixes (6s)',
    };
    return names[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const comparisons = discRep?.comparisons || [];

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 backdrop-blur-md shadow-xl overflow-hidden transition-all">
      {/* Top Banner Header */}
      <div className="p-5 border-b border-slate-800/80 bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-md">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide">
                Dual-Pipeline Analytics & External Verification
              </h3>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider border ${
                verResult?.verification_status === 'VERIFIED_CONSISTENT'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : verResult?.verification_status === 'ENRICHED_AND_RECALCULATED'
                  ? 'bg-purple-500/10 border-purple-500/30 text-purple-300'
                  : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
              }`}>
                {verResult?.verification_status?.replace(/_/g, ' ') || 'VERIFIED'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Independent Qwen/Local calculation deterministically cross-referenced against authoritative external archives.
            </p>
          </div>
        </div>

        {latencyMs > 0 && (
          <div className="px-3 py-1 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 font-mono">
            Pipeline: <strong className="text-cyan-300 font-semibold">{latencyMs.toFixed(0)}ms</strong>
          </div>
        )}
      </div>

      {/* Actual Live Processing States (Requirement 8) */}
      <div className="p-5 border-b border-slate-800/60 bg-slate-950/40">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Active Pipeline Stages</span>
          <span className="text-slate-500 text-[10px] lowercase">({states.length} triggered operations)</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {states.map((st, idx) => {
            const Icon = st.icon;
            const borderClasses = {
              emerald: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
              cyan: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300',
              amber: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
              purple: 'border-purple-500/30 bg-purple-500/10 text-purple-300',
              rose: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
            }[st.color] || 'border-slate-800 bg-slate-900 text-slate-300';

            return (
              <div
                key={st.id}
                className={`p-3 rounded-2xl border flex flex-col justify-between transition-all ${borderClasses}`}
              >
                <div className="flex items-center justify-between gap-1 mb-2">
                  <span className="text-[10px] font-mono font-bold opacity-60">0{idx + 1}</span>
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold leading-tight">{st.label}</h4>
                  <p className="text-[10px] opacity-80 mt-1 truncate">{st.detail}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Provenance & Summary Row */}
      <div className="p-5 flex flex-col gap-3">
        {verResult?.provenance_summary && (
          <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/90 text-xs text-slate-300 flex items-start gap-3">
            <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-semibold text-white">Verification Finding: </span>
              {verResult.provenance_summary}
            </div>
          </div>
        )}

        {/* Ingested Scorecards Note if enriched */}
        {verResult?.notes && verResult.notes.length > 0 && (
          <div className="flex flex-col gap-1.5 pl-1">
            {verResult.notes.map((note, i) => (
              <div key={i} className="flex items-center gap-2 text-[11px] text-slate-400">
                <FileCheck2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>{note}</span>
              </div>
            ))}
          </div>
        )}

        {/* Collapsible Field-Level Comparison Matrix (Requirement 3) */}
        <div className="mt-2 border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/60">
          <button
            type="button"
            onClick={() => setIsTableExpanded(!isTableExpanded)}
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-800/40 text-left transition"
            aria-expanded={isTableExpanded}
          >
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-200">
                Field-Level Evidence Matrix
              </span>
              <span className="text-[11px] text-slate-400">
                ({discRep?.matching_fields || comparisons.length} of {discRep?.total_fields_compared || comparisons.length} fields matching)
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-cyan-400 font-medium">
              <span>{isTableExpanded ? 'Collapse Matrix' : 'Inspect Field-by-Field'}</span>
              {isTableExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </div>
          </button>

          {isTableExpanded && (
            <div className="overflow-x-auto border-t border-slate-800/80">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-900/90 text-slate-400 text-[11px] border-b border-slate-800">
                    <th className="py-2.5 px-4 font-semibold">Metric</th>
                    <th className="py-2.5 px-4 font-semibold">
                      <span className="flex items-center gap-1">
                        <Cpu className="w-3 h-3 text-emerald-400" /> Local Result
                      </span>
                    </th>
                    <th className="py-2.5 px-4 font-semibold">
                      <span className="flex items-center gap-1">
                        <Globe className="w-3 h-3 text-cyan-400" /> External Result
                      </span>
                    </th>
                    <th className="py-2.5 px-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {comparisons.map((row) => {
                    const isMatch = row.status === 'MATCH';
                    return (
                      <tr key={row.metric} className="hover:bg-slate-800/30 transition">
                        <td className="py-2.5 px-4 font-sans font-medium text-slate-200">
                          {formatMetricName(row.metric)}
                        </td>
                        <td className="py-2.5 px-4 text-emerald-300 font-bold">
                          {row.local_value !== null && row.local_value !== undefined ? String(row.local_value) : '—'}
                        </td>
                        <td className="py-2.5 px-4 text-cyan-300 font-bold">
                          {row.external_value !== null && row.external_value !== undefined ? String(row.external_value) : '—'}
                        </td>
                        <td className="py-2.5 px-4">
                          {isMatch ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-sans font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              <CheckCircle2 className="w-3 h-3" /> Consistent
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-sans font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                              <AlertTriangle className="w-3 h-3" /> {row.status.replace(/_/g, ' ')}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
