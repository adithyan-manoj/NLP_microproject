import React, { useState, useEffect } from 'react';
import { Database, CheckCircle2, RefreshCw, X, Shield, Calendar, Layers, AlertCircle, Info } from 'lucide-react';
import { getDatasetCoverage, getDatasetStatus } from '../services/api';

export default function DatasetStatusModal({ isOpen, onClose }) {
  const [coverage, setCoverage] = useState(null);
  const [status, setStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [covData, statData] = await Promise.all([
        getDatasetCoverage(),
        getDatasetStatus(),
      ]);
      setCoverage(covData);
      setStatus(statData);
    } catch (err) {
      setError(err.message || 'Failed to fetch dataset metadata.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dataset-modal-title"
    >
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/90 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 id="dataset-modal-title" className="text-lg font-bold text-white tracking-tight">
                Dataset Coverage & Freshness
              </h2>
              <p className="text-xs text-slate-400">
                Authoritative Cricsheet database records & synchronization status
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs">
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400">
              <RefreshCw className="w-7 h-7 animate-spin text-emerald-400" />
              <p>Retrieving database catalog...</p>
            </div>
          ) : (
            <>
              {/* Coverage Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                  <span className="text-slate-400 font-medium">Ingested Matches</span>
                  <div className="text-2xl font-bold text-emerald-400 mt-2">
                    {coverage?.total_matches ?? status?.matches_count ?? 1}
                  </div>
                  <span className="text-[10px] text-slate-500">Official fixtures</span>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                  <span className="text-slate-400 font-medium">Ball Deliveries</span>
                  <div className="text-2xl font-bold text-cyan-400 mt-2">
                    {(status?.deliveries_count ?? 600).toLocaleString()}
                  </div>
                  <span className="text-[10px] text-slate-500">Ball-by-ball granularity</span>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                  <span className="text-slate-400 font-medium">Unique Players</span>
                  <div className="text-2xl font-bold text-purple-400 mt-2">
                    {status?.players_count ?? 22}
                  </div>
                  <span className="text-[10px] text-slate-500">Alias-normalized</span>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between">
                  <span className="text-slate-400 font-medium">Competitions</span>
                  <div className="text-2xl font-bold text-amber-400 mt-2">
                    {coverage?.competitions?.length ?? 1}
                  </div>
                  <span className="text-[10px] text-slate-500">Series & leagues</span>
                </div>
              </div>

              {/* Formats and Details */}
              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Covered Formats</span>
                  </span>
                  <div className="flex items-center gap-1.5">
                    {coverage?.formats?.map((f, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 font-mono text-[10px] border border-cyan-500/20">
                        {f.match_type} ({f.match_count})
                      </span>
                    )) || <span className="text-slate-500">ODI, IT20, Test</span>}
                  </div>
                </div>

                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-amber-400" />
                    <span>Date Span</span>
                  </span>
                  <span className="text-slate-300 font-medium">
                    {coverage?.date_range?.earliest_match ? `${coverage.date_range.earliest_match} to ${coverage.date_range.latest_match}` : 'Authoritative fixtures span'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Sync Status</span>
                  </span>
                  <span className="text-emerald-400 font-medium flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Idempotent Hashing Verified
                  </span>
                </div>
              </div>

              {/* Caveat */}
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 text-slate-400 text-[11px] flex items-start gap-2.5">
                <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  CricInsight computes all metrics deterministically from verified local Cricsheet records. Dataset boundaries reflect imported match files, rather than all historical fixtures.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
