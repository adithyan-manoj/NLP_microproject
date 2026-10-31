import React, { useState } from 'react';
import {
  Trophy,
  ArrowRightLeft,
  AlertTriangle,
  RotateCcw,
  CheckCircle,
  Clock,
  Sparkles,
  Users,
  Activity,
  Flame,
  X,
} from 'lucide-react';
import { recordLiveBall } from '../services/api';

export default function LiveScorepad({ match, tournament, onMatchUpdated, onClose }) {
  const [innings, setInnings] = useState(1);
  const [currentScore, setCurrentScore] = useState({
    runs: innings === 1 ? (match.innings1_runs || 0) : (match.innings2_runs || 0),
    wickets: innings === 1 ? (match.innings1_wickets || 0) : (match.innings2_wickets || 0),
    overs: innings === 1 ? (match.innings1_overs || 0.0) : (match.innings2_overs || 0.0),
  });

  const [striker, setStriker] = useState('Batter 1');
  const [nonStriker, setNonStriker] = useState('Batter 2');
  const [bowler, setBowler] = useState('Bowler 1');

  const [strikerStats, setStrikerStats] = useState({ runs: 0, balls: 0, fours: 0, sixes: 0 });
  const [nonStrikerStats, setNonStrikerStats] = useState({ runs: 0, balls: 0, fours: 0, sixes: 0 });
  const [bowlerStats, setBowlerStats] = useState({ overs: 0.0, runs: 0, wickets: 0, maidens: 0 });

  const [recentBalls, setRecentBalls] = useState([]);
  const [isWicketModalOpen, setIsWicketModalOpen] = useState(false);
  const [nextBatterName, setNextBatterName] = useState('');
  const [dismissalType, setDismissalType] = useState('bowled');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  // Compute Current Run Rate (CRR)
  const legalOvers = currentScore.overs;
  const fullOvers = Math.floor(legalOvers);
  const ballsInOver = Math.round((legalOvers - fullOvers) * 10);
  const decOvers = fullOvers + (ballsInOver / 6.0);
  const crr = decOvers > 0 ? (currentScore.runs / decOvers).toFixed(2) : '0.00';

  const handleScoreEvent = async (event) => {
    if (isSubmitting) return;

    let runsBatter = 0;
    let runsExtra = 0;
    let extraType = '';
    let isWicket = false;

    if (event === 'wicket') {
      setIsWicketModalOpen(true);
      return;
    }

    if (typeof event === 'number') {
      runsBatter = event;
    } else if (event === 'wide') {
      runsExtra = 1;
      extraType = 'wide';
    } else if (event === 'noball') {
      runsExtra = 1;
      extraType = 'noball';
    } else if (event === 'bye') {
      runsExtra = 1;
      extraType = 'bye';
    } else if (event === 'legbye') {
      runsExtra = 1;
      extraType = 'legbye';
    }

    await submitBall({
      runsBatter,
      runsExtra,
      extraType,
      isWicket: false,
      ballLabel: typeof event === 'number' ? (event === 0 ? '•' : `${event}`) : event.toUpperCase().slice(0, 2),
    });
  };

  const handleConfirmWicket = async () => {
    setIsWicketModalOpen(false);
    await submitBall({
      runsBatter: 0,
      runsExtra: 0,
      extraType: '',
      isWicket: true,
      dismissalKind: dismissalType,
      nextBatter: nextBatterName.trim() || `Batter ${currentScore.wickets + 3}`,
      ballLabel: 'W',
    });
    setNextBatterName('');
  };

  const submitBall = async ({ runsBatter, runsExtra, extraType, isWicket, dismissalKind, nextBatter, ballLabel }) => {
    setIsSubmitting(true);
    setStatusMessage(null);

    const payload = {
      innings,
      over_num: fullOvers,
      ball_num: ballsInOver + 1,
      batter_name: striker,
      bowler_name: bowler,
      non_striker_name: nonStriker,
      runs_batter: runsBatter,
      runs_extra: runsExtra,
      extra_type: extraType || '',
      is_wicket: isWicket || false,
      dismissal_kind: dismissalKind || '',
      player_dismissed: isWicket ? striker : '',
      next_batter: nextBatter || '',
    };

    try {
      const res = await recordLiveBall(match.id, payload);

      setCurrentScore({
        runs: res.total_runs,
        wickets: res.total_wickets,
        overs: res.overs,
      });

      // Update batter stats
      const isLegal = !['wide', 'noball'].includes(extraType);
      setStrikerStats((prev) => ({
        runs: prev.runs + runsBatter,
        balls: isLegal ? prev.balls + 1 : prev.balls,
        fours: runsBatter === 4 ? prev.fours + 1 : prev.fours,
        sixes: runsBatter === 6 ? prev.sixes + 1 : prev.sixes,
      }));

      // Update bowler stats
      setBowlerStats((prev) => ({
        ...prev,
        runs: prev.runs + runsBatter + runsExtra,
        wickets: isWicket ? prev.wickets + 1 : prev.wickets,
      }));

      // Update striker rotation from backend calculation
      if (res.striker && res.non_striker) {
        setStriker(res.striker);
        setNonStriker(res.non_striker);
      }

      // Add to recent deliveries ticker
      setRecentBalls((prev) => [...prev.slice(-11), { label: ballLabel, isWicket, runs: runsBatter + runsExtra }]);

      if (res.over_completed) {
        setStatusMessage(`Over completed! Strike rotated for next over.`);
      }

      if (onMatchUpdated) onMatchUpdated();
    } catch (err) {
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const manualRotateStrike = () => {
    setStriker((prev) => {
      const currentNon = nonStriker;
      setNonStriker(prev);
      return currentNon;
    });
  };

  return (
    <div className="flex flex-col gap-5 p-6 rounded-3xl bg-slate-900/90 border border-slate-800 text-slate-100 shadow-2xl backdrop-blur">
      {/* Header Info */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold">
            🏏
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-base">
                {match.team1_name || 'Team 1'} vs {match.team2_name || 'Team 2'}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 uppercase tracking-wider animate-pulse">
                LIVE SCORING
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {tournament?.name} • Inning {innings} ({tournament?.format || 'T20'})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Switch Innings */}
          <button
            type="button"
            onClick={() => setInnings((prev) => (prev === 1 ? 2 : 1))}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-cyan-300 border border-slate-700 transition"
          >
            Switch to Inn {innings === 1 ? '2' : '1'}
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Main Scoreboard Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-slate-800/80 shadow-inner">
        {/* Score & Wickets */}
        <div className="flex flex-col items-center justify-center text-center">
          <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Total Score</span>
          <div className="flex items-baseline gap-1 mt-1">
            <span className="text-4xl font-extrabold text-white tracking-tight font-mono">
              {currentScore.runs}
            </span>
            <span className="text-2xl font-bold text-emerald-400 font-mono">/ {currentScore.wickets}</span>
          </div>
        </div>

        {/* Overs & Run Rate */}
        <div className="flex flex-col items-center justify-center text-center border-y md:border-y-0 md:border-x border-slate-800/80 py-2 md:py-0">
          <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Overs</span>
          <div className="text-2xl font-bold text-slate-100 font-mono mt-1">
            {currentScore.overs.toFixed(1)} <span className="text-xs text-slate-500 font-sans">/ {tournament?.overs_limit || 20} ov</span>
          </div>
          <div className="text-xs text-cyan-400 mt-1 font-mono">
            CRR: <span className="font-semibold text-white">{crr}</span>
          </div>
        </div>

        {/* Current Bowler / Spell */}
        <div className="flex flex-col items-center justify-center text-center">
          <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Bowler Spell</span>
          <span className="font-semibold text-white text-sm mt-1">{bowler}</span>
          <div className="text-xs text-slate-400 font-mono mt-0.5">
            {bowlerStats.wickets} wkt • {bowlerStats.runs} runs
          </div>
        </div>
      </div>

      {/* Batting on Crease Tracker */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Striker */}
        <div className="p-4 rounded-xl bg-slate-950/70 border border-emerald-500/30 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400" />
            <div>
              <div className="flex items-center gap-1.5">
                <input
                  type="text"
                  value={striker}
                  onChange={(e) => setStriker(e.target.value)}
                  className="bg-transparent border-b border-transparent hover:border-slate-700 focus:border-cyan-500 focus:outline-none font-semibold text-sm text-white"
                />
                <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider bg-emerald-500/10 px-1.5 py-0.5 rounded">
                  STRIKE
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {strikerStats.runs} ({strikerStats.balls}b) • {strikerStats.fours}x4 • {strikerStats.sixes}x6
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={manualRotateStrike}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
            title="Rotate Strike"
          >
            <ArrowRightLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Non-Striker */}
        <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-600" />
            <div>
              <input
                type="text"
                value={nonStriker}
                onChange={(e) => setNonStriker(e.target.value)}
                className="bg-transparent border-b border-transparent hover:border-slate-700 focus:border-cyan-500 focus:outline-none font-semibold text-sm text-slate-300"
              />
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {nonStrikerStats.runs} ({nonStrikerStats.balls}b)
              </p>
            </div>
          </div>
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">Non-Striker</span>
        </div>
      </div>

      {/* Recent Deliveries Ticker */}
      <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 overflow-x-auto text-xs">
        <span className="text-slate-400 text-xs font-semibold whitespace-nowrap">This Over:</span>
        {recentBalls.length === 0 ? (
          <span className="text-slate-500 text-xs italic">Awaiting first delivery...</span>
        ) : (
          recentBalls.map((b, idx) => (
            <span
              key={idx}
              className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 font-mono shadow-sm ${
                b.isWicket
                  ? 'bg-rose-500 text-white animate-bounce'
                  : b.label === '4'
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  : b.label === '6'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'bg-slate-800 text-slate-200'
              }`}
            >
              {b.label}
            </span>
          ))
        )}
      </div>

      {statusMessage && (
        <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-cyan-300 text-xs flex items-center gap-2">
          <Sparkles className="w-4 h-4 flex-shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Interactive Ball-by-Ball Keypad */}
      <div className="flex flex-col gap-3 pt-2">
        <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Ball Outcome</span>
        <div className="grid grid-cols-6 gap-2">
          {[0, 1, 2, 3, 4, 6].map((run) => (
            <button
              key={run}
              type="button"
              disabled={isSubmitting}
              onClick={() => handleScoreEvent(run)}
              className={`py-3.5 rounded-xl font-bold font-mono text-base transition shadow-sm active:scale-95 disabled:opacity-50 ${
                run === 4
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-950'
                  : run === 6
                  ? 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-950'
                  : run === 0
                  ? 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                  : 'bg-slate-800 hover:bg-slate-700 text-white'
              }`}
            >
              {run === 0 ? 'DOT (0)' : run}
            </button>
          ))}
        </div>

        {/* Extras & Wicket Controls */}
        <div className="grid grid-cols-5 gap-2">
          {['wide', 'noball', 'bye', 'legbye'].map((ext) => (
            <button
              key={ext}
              type="button"
              disabled={isSubmitting}
              onClick={() => handleScoreEvent(ext)}
              className="py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-700 text-amber-300 border border-slate-700/80 text-xs font-bold uppercase tracking-wider transition active:scale-95 disabled:opacity-50"
            >
              {ext}
            </button>
          ))}
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleScoreEvent('wicket')}
            className="py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold uppercase tracking-wider transition shadow-lg shadow-rose-950/60 active:scale-95 disabled:opacity-50"
          >
            WICKET
          </button>
        </div>
      </div>

      {/* Wicket Confirmation Dialog */}
      {isWicketModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col gap-4 shadow-2xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Record Wicket Dismissal</h3>
                <p className="text-xs text-slate-400">Player dismissed: {striker}</p>
              </div>
            </div>

            <div className="flex flex-col gap-2 text-xs">
              <label className="text-slate-300 font-medium">Dismissal Kind</label>
              <select
                value={dismissalType}
                onChange={(e) => setDismissalType(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="bowled">Bowled</option>
                <option value="caught">Caught</option>
                <option value="lbw">LBW</option>
                <option value="run out">Run Out</option>
                <option value="stumped">Stumped</option>
                <option value="hit wicket">Hit Wicket</option>
              </select>
            </div>

            <div className="flex flex-col gap-2 text-xs">
              <label className="text-slate-300 font-medium">Incoming Batter Name</label>
              <input
                type="text"
                placeholder={`e.g. Batter ${currentScore.wickets + 3}`}
                value={nextBatterName}
                onChange={(e) => setNextBatterName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setIsWicketModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmWicket}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white transition shadow-md"
              >
                Confirm Wicket & Next Batter
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
