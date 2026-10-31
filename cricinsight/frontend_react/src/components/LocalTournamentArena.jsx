import React, { useState, useEffect } from 'react';
import {
  Trophy,
  Users,
  Calendar,
  Flame,
  Plus,
  ArrowRight,
  TrendingUp,
  Activity,
  Award,
  Shield,
  PlayCircle,
  FileText,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';

import {
  getTournaments,
  createTournament,
  getTournamentDetails,
  addTournamentTeam,
  createTournamentMatch,
} from '../services/api';

import LiveScorepad from './LiveScorepad';
import QuickScorecardModal from './QuickScorecardModal';

export default function LocalTournamentArena() {
  const [tournaments, setTournaments] = useState([]);
  const [activeTournament, setActiveTournament] = useState(null);
  const [activeTab, setActiveTab] = useState('standings'); // standings, fixtures, teams, leaders
  const [isLoading, setIsLoading] = useState(true);

  // Modals & Panels
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isAddTeamModalOpen, setIsAddTeamModalOpen] = useState(false);
  const [isCreateMatchModalOpen, setIsCreateMatchModalOpen] = useState(false);
  const [activeScoringMatch, setActiveScoringMatch] = useState(null);
  const [activeSummaryMatch, setActiveSummaryMatch] = useState(null);

  // Form states
  const [newTourName, setNewTourName] = useState('');
  const [newTourFormat, setNewTourFormat] = useState('T20');
  const [newTourOvers, setNewTourOvers] = useState(20);

  const [teamName, setTeamName] = useState('');
  const [teamCode, setTeamCode] = useState('');
  const [teamCaptain, setTeamCaptain] = useState('');
  const [teamColor, setTeamColor] = useState('#06B6D4');
  const [teamPlayersRaw, setTeamPlayersRaw] = useState('');

  const [matchTeam1, setMatchTeam1] = useState('');
  const [matchTeam2, setMatchTeam2] = useState('');
  const [matchVenue, setMatchVenue] = useState('City Sports Arena');
  const [matchNumber, setMatchNumber] = useState(1);

  useEffect(() => {
    fetchTournaments();
  }, []);

  const fetchTournaments = async () => {
    setIsLoading(true);
    try {
      const data = await getTournaments();
      setTournaments(data);
      if (data.length > 0) {
        loadTournamentDetails(data[0].id);
      } else {
        // Auto-seed a demo local tournament if empty
        seedDemoTournament();
      }
    } catch (err) {
      console.error('Failed to load tournaments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const seedDemoTournament = async () => {
    try {
      const demo = await createTournament({
        name: 'Monsoon Premier League 2026',
        season: '2026',
        format: 'T20',
        overs_limit: 20,
      });
      const t1 = await addTournamentTeam(demo.id, {
        name: 'Royal Challengers Club',
        short_code: 'RCC',
        captain: 'Amit Verma',
        color: '#06B6D4',
        players: ['Amit Verma', 'Ramesh Kumar', 'Karan Patel', 'Deepak Joshi'],
      });
      const t2 = await addTournamentTeam(demo.id, {
        name: 'City Super Kings',
        short_code: 'CSK',
        captain: 'Sunil Rao',
        color: '#F59E0B',
        players: ['Sunil Rao', 'Manoj Nair', 'Vikas Sharma', 'Pradeep Roy'],
      });
      await createTournamentMatch(demo.id, {
        team1_id: t1.id,
        team2_id: t2.id,
        venue: 'Eden Park Grounds',
        match_number: 1,
      });
      const fresh = await getTournaments();
      setTournaments(fresh);
      loadTournamentDetails(demo.id);
    } catch (e) {
      console.error('Could not seed demo tournament:', e);
    }
  };

  const loadTournamentDetails = async (id) => {
    try {
      const details = await getTournamentDetails(id);
      setActiveTournament(details);
    } catch (err) {
      console.error('Failed to load tournament details:', err);
    }
  };

  const handleCreateTournament = async (e) => {
    e.preventDefault();
    if (!newTourName.trim()) return;
    try {
      const created = await createTournament({
        name: newTourName.trim(),
        season: '2026',
        format: newTourFormat,
        overs_limit: Number(newTourOvers),
      });
      setIsCreateModalOpen(false);
      setNewTourName('');
      const updatedList = await getTournaments();
      setTournaments(updatedList);
      loadTournamentDetails(created.id);
    } catch (err) {
      alert(`Error creating tournament: ${err.message}`);
    }
  };

  const handleAddTeam = async (e) => {
    e.preventDefault();
    if (!teamName.trim() || !teamCode.trim()) return;
    try {
      const playersList = teamPlayersRaw
        .split(',')
        .map((p) => p.trim())
        .filter(Boolean);

      await addTournamentTeam(activeTournament.id, {
        name: teamName.trim(),
        short_code: teamCode.trim().toUpperCase(),
        captain: teamCaptain.trim(),
        color: teamColor,
        players: playersList,
      });

      setIsAddTeamModalOpen(false);
      setTeamName('');
      setTeamCode('');
      setTeamCaptain('');
      setTeamPlayersRaw('');
      loadTournamentDetails(activeTournament.id);
    } catch (err) {
      alert(`Error adding team: ${err.message}`);
    }
  };

  const handleCreateMatch = async (e) => {
    e.preventDefault();
    if (!matchTeam1 || !matchTeam2 || matchTeam1 === matchTeam2) {
      alert('Please select two distinct teams for the match.');
      return;
    }
    try {
      await createTournamentMatch(activeTournament.id, {
        team1_id: matchTeam1,
        team2_id: matchTeam2,
        venue: matchVenue,
        match_number: Number(matchNumber),
      });
      setIsCreateMatchModalOpen(false);
      loadTournamentDetails(activeTournament.id);
    } catch (err) {
      alert(`Error creating match: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Top Banner & League Switcher */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl backdrop-blur">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-2xl shadow-lg shadow-amber-950/40">
            🏆
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                {activeTournament?.name || 'Local Tournament Arena'}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider">
                {activeTournament?.format || 'T20'} • {activeTournament?.season || '2026'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage local leagues, record live scorecards, view real-time standings & NRR.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Tournament Switcher Dropdown */}
          <select
            value={activeTournament?.id || ''}
            onChange={(e) => loadTournamentDetails(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 font-semibold focus:outline-none focus:border-cyan-500"
          >
            {tournaments.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          {/* New Tournament Button */}
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 text-xs font-bold transition shadow-md shadow-cyan-950"
          >
            <Plus className="w-4 h-4" />
            <span>New Tournament</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800/80 pb-2 text-xs">
        {[
          { id: 'standings', label: 'Points Table & Standings', icon: Trophy },
          { id: 'fixtures', label: 'Match Center & Fixtures', icon: Calendar },
          { id: 'leaders', label: 'Orange & Purple Caps', icon: Award },
          { id: 'teams', label: 'Teams & Rosters', icon: Users },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold transition ${
                isActive
                  ? 'bg-slate-800 text-cyan-300 border border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Active Live Scorepad (if active) */}
      {activeScoringMatch && (
        <LiveScorepad
          match={activeScoringMatch}
          tournament={activeTournament}
          onMatchUpdated={() => loadTournamentDetails(activeTournament.id)}
          onClose={() => setActiveScoringMatch(null)}
        />
      )}

      {/* TAB 1: Points Table & Standings */}
      {activeTab === 'standings' && (
        <div className="flex flex-col gap-6">
          <div className="rounded-3xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-xl backdrop-blur">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-white text-base">Tournament Points Table</h3>
                <p className="text-xs text-slate-400">
                  Ranked by: Points ➔ Net Run Rate (NRR) ➔ Wins
                </p>
              </div>
              <button
                type="button"
                onClick={() => loadTournamentDetails(activeTournament.id)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                title="Refresh Table"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4 text-center">Pos</th>
                    <th className="py-3 px-4">Team</th>
                    <th className="py-3 px-4 text-center">P</th>
                    <th className="py-3 px-4 text-center">W</th>
                    <th className="py-3 px-4 text-center">L</th>
                    <th className="py-3 px-4 text-center">Tied</th>
                    <th className="py-3 px-4 text-center">NRR</th>
                    <th className="py-3 px-4 text-center">For</th>
                    <th className="py-3 px-4 text-center">Against</th>
                    <th className="py-3 px-4 text-center font-bold text-cyan-400">PTS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {(!activeTournament?.standings || activeTournament.standings.length === 0) ? (
                    <tr>
                      <td colSpan="10" className="py-8 text-center text-slate-500 font-sans italic">
                        No matches played yet. Start a match in the Match Center to calculate standings!
                      </td>
                    </tr>
                  ) : (
                    activeTournament.standings.map((s, idx) => (
                      <tr
                        key={s.team_id}
                        className={`hover:bg-slate-800/40 transition ${
                          idx < 2 ? 'bg-emerald-500/[0.03]' : ''
                        }`}
                      >
                        <td className="py-3.5 px-4 text-center font-bold text-slate-300">
                          {idx + 1}
                        </td>
                        <td className="py-3.5 px-4 font-sans font-bold text-white flex items-center gap-2.5">
                          <span
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: s.color || '#06B6D4' }}
                          />
                          <span>{s.team_name}</span>
                          <span className="text-[10px] text-slate-400 font-mono">({s.short_code})</span>
                        </td>
                        <td className="py-3.5 px-4 text-center text-slate-300">{s.played}</td>
                        <td className="py-3.5 px-4 text-center font-semibold text-emerald-400">{s.won}</td>
                        <td className="py-3.5 px-4 text-center text-rose-400">{s.lost}</td>
                        <td className="py-3.5 px-4 text-center text-slate-400">{s.tied}</td>
                        <td className={`py-3.5 px-4 text-center font-bold ${
                          s.nrr > 0 ? 'text-emerald-400' : s.nrr < 0 ? 'text-rose-400' : 'text-slate-400'
                        }`}>
                          {s.nrr > 0 ? `+${s.nrr.toFixed(3)}` : s.nrr.toFixed(3)}
                        </td>
                        <td className="py-3.5 px-4 text-center text-slate-400">
                          {s.runs_for}/{s.overs_for}
                        </td>
                        <td className="py-3.5 px-4 text-center text-slate-400">
                          {s.runs_against}/{s.overs_against}
                        </td>
                        <td className="py-3.5 px-4 text-center font-extrabold text-cyan-300 text-sm">
                          {s.points}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Match Center & Fixtures */}
      {activeTab === 'fixtures' && (
        <div className="flex flex-col gap-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white text-base">Tournament Fixtures & Scorecards</h3>
              <p className="text-xs text-slate-400">Launch live ball-by-ball scorepad or enter quick post-match summaries.</p>
            </div>
            <button
              type="button"
              onClick={() => setIsCreateMatchModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-xs font-semibold transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Match Fixture</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(!activeTournament?.matches || activeTournament.matches.length === 0) ? (
              <div className="col-span-2 p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-500 text-xs">
                No fixtures scheduled yet. Click &quot;Add Match Fixture&quot; above to schedule your first game!
              </div>
            ) : (
              activeTournament.matches.map((m) => (
                <div
                  key={m.id}
                  className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 flex flex-col gap-3 shadow-lg hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Match #{m.match_number} • {m.match_date}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        m.status === 'live'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse'
                          : m.status === 'completed'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {m.status}
                    </span>
                  </div>

                  <div className="flex flex-col gap-2 my-1">
                    {/* Team 1 Score */}
                    <div className="flex items-center justify-between font-bold text-sm text-white">
                      <span>{m.team1_name || 'Team 1'}</span>
                      <span className="font-mono text-cyan-300">
                        {m.innings1_runs > 0 || m.status === 'completed'
                          ? `${m.innings1_runs}/${m.innings1_wickets} (${m.innings1_overs} ov)`
                          : 'Yet to bat'}
                      </span>
                    </div>

                    {/* Team 2 Score */}
                    <div className="flex items-center justify-between font-bold text-sm text-white">
                      <span>{m.team2_name || 'Team 2'}</span>
                      <span className="font-mono text-emerald-300">
                        {m.innings2_runs > 0 || m.status === 'completed'
                          ? `${m.innings2_runs}/${m.innings2_wickets} (${m.innings2_overs} ov)`
                          : 'Yet to bat'}
                      </span>
                    </div>
                  </div>

                  {m.winner_name && (
                    <div className="text-xs text-amber-300 font-semibold flex items-center gap-1.5 pt-2 border-t border-slate-800/80">
                      <Trophy className="w-3.5 h-3.5" />
                      <span>{m.winner_name} won {m.margin}</span>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2 mt-auto">
                    <button
                      type="button"
                      onClick={() => setActiveScoringMatch(m)}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold text-xs transition shadow-md shadow-emerald-950"
                    >
                      <PlayCircle className="w-4 h-4" />
                      <span>Live Scoring Pad</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveSummaryMatch(m)}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition border border-slate-700"
                    >
                      <FileText className="w-4 h-4" />
                      <span>Quick Scorecard</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 3: Orange & Purple Caps */}
      {activeTab === 'leaders' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Orange Cap (Most Runs) */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-amber-500/30 flex flex-col gap-4 shadow-xl backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-xl font-bold">
                🧢
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Orange Cap — Top Run Scorers</h3>
                <p className="text-xs text-slate-400">Leading batsmen across all tournament matches</p>
              </div>
            </div>

            {(!activeTournament?.leaderboard?.orange_cap || activeTournament.leaderboard.orange_cap.length === 0) ? (
              <p className="text-xs text-slate-500 italic py-4 text-center">
                Record scorecards to generate Orange Cap leaderboard!
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {activeTournament.leaderboard.orange_cap.map((p, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs font-mono"
                  >
                    <div className="flex items-center gap-2.5 font-sans">
                      <span className="font-bold text-amber-400 w-4">{idx + 1}</span>
                      <span className="font-semibold text-white">{p.player_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400">SR: {p.strike_rate}</span>
                      <span className="font-bold text-amber-300 text-sm">{p.runs} runs</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Purple Cap (Most Wickets) */}
          <div className="p-6 rounded-3xl bg-slate-900/60 border border-purple-500/30 flex flex-col gap-4 shadow-xl backdrop-blur">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 text-xl font-bold">
                🟣
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Purple Cap — Top Wicket Takers</h3>
                <p className="text-xs text-slate-400">Leading bowlers across all tournament matches</p>
              </div>
            </div>

            {(!activeTournament?.leaderboard?.purple_cap || activeTournament.leaderboard.purple_cap.length === 0) ? (
              <p className="text-xs text-slate-500 italic py-4 text-center">
                Record scorecards to generate Purple Cap leaderboard!
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {activeTournament.leaderboard.purple_cap.map((p, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs font-mono"
                  >
                    <div className="flex items-center gap-2.5 font-sans">
                      <span className="font-bold text-purple-400 w-4">{idx + 1}</span>
                      <span className="font-semibold text-white">{p.player_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400">Econ: {p.economy}</span>
                      <span className="font-bold text-purple-300 text-sm">{p.wickets} wkts</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: Teams & Squads */}
      {activeTab === 'teams' && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white text-base">Registered Teams & Rosters</h3>
              <p className="text-xs text-slate-400">View team captains, colors, and squad rosters.</p>
            </div>
            <button
              type="button"
              onClick={() => setIsAddTeamModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold text-xs transition shadow-md shadow-cyan-950"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Register Team</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {(!activeTournament?.teams || activeTournament.teams.length === 0) ? (
              <div className="col-span-3 p-8 rounded-2xl bg-slate-900/40 border border-slate-800 text-center text-slate-500 text-xs">
                No teams registered yet. Click &quot;Register Team&quot; above to add teams to this tournament.
              </div>
            ) : (
              activeTournament.teams.map((t) => (
                <div
                  key={t.id}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col gap-3"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className="w-4 h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: t.color || '#06B6D4' }}
                    />
                    <div>
                      <h4 className="font-bold text-white text-sm">{t.name}</h4>
                      <p className="text-xs text-slate-400 font-mono">Code: {t.short_code}</p>
                    </div>
                  </div>
                  {t.captain && (
                    <div className="text-xs text-slate-300 pt-2 border-t border-slate-800/80">
                      Captain: <span className="font-semibold text-white">{t.captain}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* MODAL 1: Create Tournament */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col gap-4 shadow-2xl">
            <h3 className="font-bold text-white text-base">Create New Local Tournament</h3>
            <form onSubmit={handleCreateTournament} className="flex flex-col gap-3 text-xs">
              <div>
                <label className="text-slate-400">Tournament Name</label>
                <input
                  type="text"
                  placeholder="e.g. Inter-College Trophy 2026"
                  value={newTourName}
                  onChange={(e) => setNewTourName(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400">Format</label>
                  <select
                    value={newTourFormat}
                    onChange={(e) => setNewTourFormat(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200"
                  >
                    <option value="T20">T20 (20 Overs)</option>
                    <option value="T10">T10 (10 Overs)</option>
                    <option value="ODI">ODI (50 Overs)</option>
                    <option value="10-over">Gully (10 Overs)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400">Overs Limit</label>
                  <input
                    type="number"
                    value={newTourOvers}
                    onChange={(e) => setNewTourOvers(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold transition shadow-md shadow-cyan-950"
                >
                  Create Tournament
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Register Team */}
      {isAddTeamModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col gap-4 shadow-2xl">
            <h3 className="font-bold text-white text-base">Register Team in {activeTournament?.name}</h3>
            <form onSubmit={handleAddTeam} className="flex flex-col gap-3 text-xs">
              <div>
                <label className="text-slate-400">Team Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Royal Warriors CC"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400">Short Code</label>
                  <input
                    type="text"
                    placeholder="e.g. RW"
                    value={teamCode}
                    onChange={(e) => setTeamCode(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white uppercase font-mono"
                    required
                  />
                </div>
                <div>
                  <label className="text-slate-400">Captain Name</label>
                  <input
                    type="text"
                    placeholder="Captain"
                    value={teamCaptain}
                    onChange={(e) => setTeamCaptain(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400">Player Roster (comma-separated)</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Virat, Rohit, Rahul, Bumrah"
                  value={teamPlayersRaw}
                  onChange={(e) => setTeamPlayersRaw(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsAddTeamModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold transition shadow-md shadow-emerald-950"
                >
                  Save Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Create Match */}
      {isCreateMatchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col gap-4 shadow-2xl">
            <h3 className="font-bold text-white text-base">Schedule New Match Fixture</h3>
            <form onSubmit={handleCreateMatch} className="flex flex-col gap-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400">Team 1</label>
                  <select
                    value={matchTeam1}
                    onChange={(e) => setMatchTeam1(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  >
                    <option value="">Select Team 1</option>
                    {activeTournament?.teams?.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-slate-400">Team 2</label>
                  <select
                    value={matchTeam2}
                    onChange={(e) => setMatchTeam2(e.target.value)}
                    className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200"
                    required
                  >
                    <option value="">Select Team 2</option>
                    {activeTournament?.teams?.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400">Venue</label>
                <input
                  type="text"
                  value={matchVenue}
                  onChange={(e) => setMatchVenue(e.target.value)}
                  className="w-full mt-1 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateMatchModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold transition shadow-md shadow-cyan-950"
                >
                  Schedule Match
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: Quick Scorecard */}
      {activeSummaryMatch && (
        <QuickScorecardModal
          match={activeSummaryMatch}
          tournament={activeTournament}
          onClose={() => setActiveSummaryMatch(null)}
          onScorecardSaved={() => {
            loadTournamentDetails(activeTournament.id);
            setActiveSummaryMatch(null);
          }}
        />
      )}
    </div>
  );
}
