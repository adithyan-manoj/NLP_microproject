import React, { useState, useRef, useEffect } from 'react';
import { Search, Sparkles, X, ArrowRight, Filter, Command } from 'lucide-react';

export default function QueryInput({ onSearch, isLoading, activeFormat, onFormatChange }) {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  // Global keyboard shortcut to focus search: '/' or 'Ctrl+K' / 'Cmd+K'
  useEffect(() => {
    const handleKeyDownGlobal = (e) => {
      if ((e.key === '/' && document.activeElement !== inputRef.current) ||
          ((e.ctrlKey || e.metaKey) && e.key === 'k')) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDownGlobal);
    return () => window.removeEventListener('keydown', handleKeyDownGlobal);
  }, []);

  const handleSubmit = (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    const trimmed = query.trim();
    if (!trimmed || isLoading) return;
    onSearch(trimmed);
  };

  const handleKeyDown = (e) => {
    // IME-safe enter-to-submit
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.isComposing || e.keyCode === 229) {
        return;
      }
      handleSubmit(e);
    }
  };

  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  const formats = [
    { id: 'all', label: 'All Formats' },
    { id: 'IPL', label: 'IPL / T20 Leagues' },
    { id: 'T20', label: 'T20 Internationals' },
    { id: 'ODI', label: 'One Day Internationals' },
    { id: 'Test', label: 'Test Matches' },
  ];

  return (
    <div className="w-full flex flex-col gap-2.5">
      {/* Format Filter Tabs */}
      {onFormatChange && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-500 flex items-center gap-1 text-[11px] font-medium mr-1">
            <Filter className="w-3 h-3" /> Scope:
          </span>
          {formats.map((fmt) => {
            const isSelected = activeFormat === fmt.id;
            return (
              <button
                key={fmt.id}
                type="button"
                onClick={() => onFormatChange(fmt.id)}
                className={`px-2.5 py-1 rounded-lg font-medium text-[11px] transition whitespace-nowrap ${
                  isSelected
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                    : 'bg-slate-950/70 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {fmt.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Main Search Input */}
      <form onSubmit={handleSubmit} className="relative group">
        <label htmlFor="cricket-nl-query" className="sr-only">
          Ask any cricket analytics or statistical query
        </label>

        <div className="relative flex items-center">
          <div className="absolute left-4 pointer-events-none text-cyan-400 flex items-center justify-center">
            <Search className="w-5 h-5" />
          </div>

          <input
            id="cricket-nl-query"
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything (e.g. 'Show me Virat Kohli\'s IPL statistics in 2022' or 'Compare Rohit and Kohli in ODIs')"
            disabled={isLoading}
            autoComplete="off"
            className="w-full pl-12 pr-36 py-4 bg-slate-900/90 text-slate-100 placeholder-slate-500 rounded-2xl border border-slate-700/80 hover:border-cyan-500/50 focus:border-cyan-400 focus:ring-4 focus:ring-cyan-500/10 focus:outline-none transition-all shadow-xl shadow-slate-950/60 text-sm sm:text-base font-sans"
          />

          <div className="absolute right-3 flex items-center gap-2">
            {!query && !isLoading && (
              <span className="hidden md:inline-flex items-center text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-400 border border-slate-700/80 select-none">
                Ctrl+K
              </span>
            )}

            {query && !isLoading && (
              <button
                type="button"
                onClick={handleClear}
                aria-label="Clear query input"
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-400 to-teal-400 hover:from-cyan-300 hover:to-teal-300 text-slate-950 font-bold text-xs sm:text-sm shadow-md shadow-cyan-950/50 disabled:opacity-40 disabled:cursor-not-allowed transition transform active:scale-95"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Analyze</span>
                  <ArrowRight className="w-3.5 h-3.5 hidden sm:inline" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
