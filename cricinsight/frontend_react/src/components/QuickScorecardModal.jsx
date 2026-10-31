import React, { useState } from 'react';
import { Trophy, CheckCircle, AlertCircle, X, Plus, Trash2 } from 'lucide-react';
import { recordMatchScorecard } from '../services/api';

export default function QuickScorecardModal({ match, tournament, onClose, onScorecardSaved }) {
  const [tossWinner, setTossWinner] = useState(match.team1_id);
  const [tossDecision, setTossDecision] = useState('bat');
  const [winnerTeamId, setWinnerTeamId] = useState(match.team1_id);
  const [margin, setMargin] = useState('by 20 runs');

  const [inn1Runs, setInn1Runs] = useState(165);
  const [inn1Wickets, setInn1Wickets] = useState(5);
  const [inn1Overs, setInn1Overs] = useState(20.0);

  const [inn2Runs, setInn2Runs] = useState(145);
  const [inn2Wickets, setInn2Wickets] = useState(8);
  const [inn2Overs, setInn2Overs] = useState(20.0);

  const [players, setPlayers] = useState([
    {
      team_id: match.team1_id,
      player_name: 'Top Batter',
      runs: 75,
      balls: 48,
      fours: 8,
      sixes: 3,
      overs_bowled: 0,
      maidens: 0,
      runs_conceded: 0,
      wickets: 0,
      is_out: false,
    },
    {
      team_id: match.team2_id,
      player_name: 'Lead Bowler',
      runs: 10,
      balls: 8,
      fours: 1,
      sixes: 0,
      overs_bowled: 4.0,
      maidens: 0,
      runs_conceded: 24,
      wickets: 3,
      is_out: true,
    },
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleAddPlayer = () => {
    setPlayers((prev) => [
      ...prev,
      {
        team_id: match.team1_id,
        player_name: '',
        runs: 0,
        balls: 0,
        fours: 0,
        sixes: 0,
        overs_bowled: 0,
        maidens: 0,
        runs_conceded: 0,
        wickets: 0,
        is_out: false,
      },
    ]);
  };

  const handleRemovePlayer = (idx) => {
    setPlayers((prev) => prev.filter((_, i) => i !== idx));
  };

  const handlePlayerChange = (idx, field, value) => {
    setPlayers((prev) => {
      const copy = [...prev];
      copy[idx] = { ...copy[idx], [field]: value };
      return copy;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const payload = {
      toss_winner_id: tossWinner,
      toss_decision: tossDecision,
      winner_team_id: winnerTeamId,
      margin,
      innings1_runs: Number(inn1Runs),
      innings1_wickets: Number(inn1Wickets),
      innings1_overs: Number(inn1Overs),
      innings2_runs: Number(inn2Runs),
      innings2_wickets: Number(inn2Wickets),
      innings2_overs: Number(inn2Overs),
      scorecards: players
        .filter((p) => p.player_name.trim() !== '')
        .map((p) => ({
          ...p,
          runs: Number(p.runs),
          balls: Number(p.balls),
          fours: Number(p.fours),
          sixes: Number(p.sixes),
          overs_bowled: Number(p.overs_bowled),
          maidens: Number(p.maidens),
          runs_conceded: Number(p.runs_conceded),
          wickets: Number(p.wickets),
        })),
    };

    try {
      await recordMatchScorecard(match.id, payload);
      if (onScorecardSaved) onScorecardSaved();
      if (onClose) onClose();
    } catch (err) {
      setError(err.message || 'Failed to record match scorecard');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col gap-5 shadow-2xl text-slate-100">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Quick Scorecard Summary Entry</h3>
              <p className="text-xs text-slate-400">
                {match.team1_name} vs {match.team2_name} • Match #{match.match_number}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 text-xs">
          {/* Innings Totals Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-2xl bg-slate-950/60 border border-slate-800">
            {/* Innings 1 */}
            <div className="flex flex-col gap-2">
              <span className="font-semibold text-cyan-300 text-xs">
                Innings 1 ({match.team1_name})
              </span>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-[11px] text-slate-400">Runs</label>
                  <input
                    type="number"
                    value={inn1Runs}
                    onChange={(e) => setInn1Runs(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400">Wickets</label>
                  <input
                    type="number"
                    value={inn1Wickets}
                    onChange={(e) => setInn1Wickets(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400">Overs</label>
                  <input
                    type="number"
                    step="0.1"
                    value={inn1Overs}
                    onChange={(e) => setInn1Overs(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Innings 2 */}
            <div className="flex flex-col gap-2">
              <span className="font-semibold text-emerald-300 text-xs">
                Innings 2 ({match.team2_name})
              </span>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-[11px] text-slate-400">Runs</label>
                  <input
                    type="number"
                    value={inn2Runs}
                    onChange={(e) => setInn2Runs(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400">Wickets</label>
                  <input
                    type="number"
                    value={inn2Wickets}
                    onChange={(e) => setInn2Wickets(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400">Overs</label>
                  <input
                    type="number"
                    step="0.1"
                    value={inn2Overs}
                    onChange={(e) => setInn2Overs(e.target.value)}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono"
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Outcome & Result */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-slate-400">Match Winner</label>
              <select
                value={winnerTeamId}
                onChange={(e) => setWinnerTeamId(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200"
              >
                <option value={match.team1_id}>{match.team1_name}</option>
                <option value={match.team2_id}>{match.team2_name}</option>
                <option value="tie">Match Tied</option>
                <option value="no_result">No Result</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400">Margin</label>
              <input
                type="text"
                placeholder="e.g. by 25 runs"
                value={margin}
                onChange={(e) => setMargin(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
              />
            </div>
            <div>
              <label className="text-slate-400">Toss Winner</label>
              <select
                value={tossWinner}
                onChange={(e) => setTossWinner(e.target.value)}
                className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200"
              >
                <option value={match.team1_id}>{match.team1_name}</option>
                <option value={match.team2_id}>{match.team2_name}</option>
              </select>
            </div>
          </div>

          {/* Individual Player Highlights */}
          <div className="flex flex-col gap-2 mt-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-300">
                Key Player Performances (For Orange & Purple Cap Rankings)
              </span>
              <button
                type="button"
                onClick={handleAddPlayer}
                className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Player
              </button>
            </div>

            <div className="flex flex-col gap-2 max-h-52 overflow-y-auto pr-1">
              {players.map((p, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-12 gap-2 p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/80 items-center text-xs"
                >
                  <div className="col-span-3">
                    <input
                      type="text"
                      placeholder="Player Name"
                      value={p.player_name}
                      onChange={(e) => handlePlayerChange(idx, 'player_name', e.target.value)}
                      className="w-full px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-white"
                    />
                  </div>
                  <div className="col-span-2">
                    <select
                      value={p.team_id}
                      onChange={(e) => handlePlayerChange(idx, 'team_id', e.target.value)}
                      className="w-full px-2 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-[11px]"
                    >
                      <option value={match.team1_id}>{match.team1_code || 'Team 1'}</option>
                      <option value={match.team2_id}>{match.team2_code || 'Team 2'}</option>
                    </select>
                  </div>
                  <div className="col-span-2 flex items-center gap-1">
                    <span className="text-[10px] text-slate-500">R:</span>
                    <input
                      type="number"
                      placeholder="Runs"
                      value={p.runs}
                      onChange={(e) => handlePlayerChange(idx, 'runs', e.target.value)}
                      className="w-full px-1.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-center"
                    />
                  </div>
                  <div className="col-span-2 flex items-center gap-1">
                    <span className="text-[10px] text-slate-500">W:</span>
                    <input
                      type="number"
                      placeholder="Wkts"
                      value={p.wickets}
                      onChange={(e) => handlePlayerChange(idx, 'wickets', e.target.value)}
                      className="w-full px-1.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-center"
                    />
                  </div>
                  <div className="col-span-2 flex items-center gap-1">
                    <span className="text-[10px] text-slate-500">Ov:</span>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="Ov"
                      value={p.overs_bowled}
                      onChange={(e) => handlePlayerChange(idx, 'overs_bowled', e.target.value)}
                      className="w-full px-1.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-white font-mono text-center"
                    />
                  </div>
                  <div className="col-span-1 flex justify-end">
                    <button
                      type="button"
                      onClick={() => handleRemovePlayer(idx)}
                      className="p-1 text-slate-500 hover:text-rose-400 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold transition shadow-lg shadow-cyan-950 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save & Update Standings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
