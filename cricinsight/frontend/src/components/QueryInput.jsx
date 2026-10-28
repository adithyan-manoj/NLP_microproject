import React, { useState, useRef } from 'react';
import { Search, Sparkles, X, CornerDownLeft, ArrowRight } from 'lucide-react';

const SUGGESTIONS = [
  "How has Virat Kohli performed against Australia in ODIs?",
  "Compare Rohit Sharma and Virat Kohli in T20 internationals",
  "Show Kohli's last 10 innings as a line chart",
  "David Warner vs Pakistan in ODIs",
  "Babar Azam batting stats in T20 matches",
];

export default function QueryInput({ onSearch, isLoading }) {
  const [query, setQuery] = useState('');
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    const trimmed = query.trim();
    if (!trimmed || isLoading) return;
    onSearch(trimmed);
  };

  const handleKeyDown = (e) => {
    // IME-safe enter-to-submit pattern:
    // Prevent submission during IME character composition (Japanese/Chinese/Korean or virtual keyboard candidate picking)
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.isComposing || e.keyCode === 229) {
        return;
      }
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    if (inputRef.current) {
      inputRef.current.focus();
    }
    onSearch(suggestion);
  };

  const handleClear = () => {
    setQuery('');
    if (inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <div className="w-full flex flex-col gap-3">
      <form onSubmit={handleSubmit} className="relative group">
        <label htmlFor="cricket-nl-query" className="sr-only">
          Ask a cricket analytics question
        </label>

        <div className="relative flex items-center">
          <div className="absolute left-4 pointer-events-none text-emerald-400 flex items-center justify-center">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>

          <input
            id="cricket-nl-query"
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything (e.g. 'How has Virat Kohli performed against Australia in ODIs?')"
            disabled={isLoading}
            autoComplete="off"
            className="w-full pl-12 pr-28 py-4 bg-slate-900/90 text-slate-100 placeholder-slate-500 rounded-2xl border border-slate-700/80 hover:border-emerald-500/50 focus:border-emerald-400 focus:ring-4 focus:ring-emerald-500/10 focus:outline-none transition-all shadow-xl shadow-slate-950/50 text-base md:text-lg backdrop-blur"
          />

          <div className="absolute right-3 flex items-center gap-2">
            {query && !isLoading && (
              <button
                type="button"
                onClick={handleClear}
                aria-label="Clear input"
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-semibold text-sm shadow-md shadow-emerald-950/50 disabled:opacity-40 disabled:cursor-not-allowed transition transform active:scale-95"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Analyze</span>
                  <ArrowRight className="w-4 h-4 hidden sm:inline" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Suggestion Chips */}
      <div className="flex items-center gap-2 flex-wrap text-xs">
        <span className="text-slate-500 font-medium flex items-center gap-1">
          <Search className="w-3 h-3" /> Try:
        </span>
        {SUGGESTIONS.map((suggestion, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => handleSuggestionClick(suggestion)}
            className="px-2.5 py-1 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800/80 hover:border-emerald-500/30 text-slate-400 hover:text-emerald-300 transition-colors text-left truncate max-w-[280px] md:max-w-none"
          >
            "{suggestion}"
          </button>
        ))}
      </div>
    </div>
  );
}
