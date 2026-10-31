import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import QueryInput from '../components/QueryInput';
import StatCards from '../components/StatCards';
import QueryScopeBadge from '../components/QueryScopeBadge';
import InsightPanel from '../components/InsightPanel';
import NLPTransparencyCard from '../components/NLPTransparencyCard';
import LiveScorepad from '../components/LiveScorepad';
import QuickScorecardModal from '../components/QuickScorecardModal';

describe('CricInsight Frontend Component Suite', () => {
  it('renders QueryInput and allows typing and submit', () => {
    const handleSearch = vi.fn();
    render(<QueryInput onSearch={handleSearch} isLoading={false} />);

    const input = screen.getByPlaceholderText(/Ask anything/i);
    expect(input).toBeInTheDocument();

    fireEvent.change(input, { target: { value: 'Kohli vs Australia in ODIs' } });
    expect(input.value).toBe('Kohli vs Australia in ODIs');

    const submitBtn = screen.getByRole('button', { name: /Analyze/i });
    fireEvent.click(submitBtn);

    expect(handleSearch).toHaveBeenCalledWith('Kohli vs Australia in ODIs');
  });

  it('renders StatCards with proper metrics', () => {
    const sampleStats = {
      total_runs: 9900,
      balls_faced: 10030,
      batting_average: 58.2,
      strike_rate: 98.7,
      high_score: 183,
      high_score_not_out: true,
      innings_count: 220,
      dismissals: 170,
      std_deviation: 31.4,
      consistency_rating: 'Moderate spread',
      fours: 920,
      sixes: 110,
      boundary_runs: 4340,
      centuries: 28,
      fifties: 55,
    };

    render(<StatCards stats={sampleStats} />);
    expect(screen.getByText('9,900')).toBeInTheDocument();
    expect(screen.getByText('58.20')).toBeInTheDocument();
    expect(screen.getByText('98.7')).toBeInTheDocument();
    expect(screen.getByText('183*')).toBeInTheDocument();
  });

  it('renders QueryScopeBadge tags correctly', () => {
    const scope = {
      players: ['Virat Kohli'],
      format: 'ODI',
      opponent: 'Australia',
      date_range: '2017 to 2024',
      analysis_type: 'Progression',
    };

    render(<QueryScopeBadge scope={scope} />);
    expect(screen.getByText('Virat Kohli')).toBeInTheDocument();
    expect(screen.getByText('ODI')).toBeInTheDocument();
    expect(screen.getByText('vs Australia')).toBeInTheDocument();
  });

  it('renders InsightPanel with analytical grounded commentary', () => {
    const insight = "Virat Kohli maintained high consistency scoring 9,900 runs.";
    const obs = ["920 fours hit", "28 centuries scored"];

    render(<InsightPanel insight={insight} observations={obs} />);
    expect(screen.getByText(insight)).toBeInTheDocument();
    expect(screen.getByText('920 fours hit')).toBeInTheDocument();
    expect(screen.getByText('28 centuries scored')).toBeInTheDocument();
  });

  it('renders NLPTransparencyCard with confidence score and toggleable trace', () => {
    const interpretation = {
      intent: 'comparison',
      players: ['Virat Kohli', 'Rohit Sharma'],
      format: 'ODI',
      last_n_innings: 10,
    };
    const confidence = {
      overall: 0.94,
      model_reported: 0.95,
      entity_resolution: 0.98,
      temporal: 1.0,
      schema_validation: 1.0,
    };
    const provider = {
      name: 'Google Gemini',
      model: 'gemini-2.5-flash',
      latency_ms: 240,
    };

    render(
      <NLPTransparencyCard
        interpretation={interpretation}
        confidence={confidence}
        provider={provider}
        status="success"
        clarificationRequired={false}
      />
    );

    expect(screen.getByText(/NLP Query Interpretation/i)).toBeInTheDocument();
    expect(screen.getByText(/94% Calibrated Confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/comparison/i)).toBeInTheDocument();

    // Click to expand trace
    const toggleBtn = screen.getByRole('button');
    fireEvent.click(toggleBtn);

    expect(screen.getByText('Virat Kohli, Rohit Sharma')).toBeInTheDocument();
    expect(screen.getByText('Virat Kohli, Rohit Sharma')).toBeInTheDocument();
    expect(screen.getByText('Last 10 Innings')).toBeInTheDocument();
    expect(screen.getByText(/Confidence Calibration Metrics/i)).toBeInTheDocument();
  });

  it('renders LiveScorepad with match header and keypad buttons', () => {
    const sampleMatch = {
      id: 'match_test_1',
      team1_name: 'Strikers',
      team2_name: 'Warriors',
      innings1_runs: 45,
      innings1_wickets: 2,
      innings1_overs: 5.2,
    };
    const sampleTour = {
      name: 'College League',
      format: 'T20',
      overs_limit: 20,
    };

    render(
      <LiveScorepad
        match={sampleMatch}
        tournament={sampleTour}
      />
    );

    expect(screen.getByText(/Strikers vs Warriors/i)).toBeInTheDocument();
    expect(screen.getByText('LIVE SCORING')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByText('/ 2')).toBeInTheDocument();
    expect(screen.getByText('DOT (0)')).toBeInTheDocument();
    expect(screen.getByText('WICKET')).toBeInTheDocument();
  });

  it('renders QuickScorecardModal with summary inputs', () => {
    const sampleMatch = {
      id: 'match_test_1',
      team1_id: 'team_1',
      team2_id: 'team_2',
      team1_name: 'Strikers',
      team2_name: 'Warriors',
      match_number: 3,
    };

    render(
      <QuickScorecardModal
        match={sampleMatch}
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText(/Quick Scorecard Summary Entry/i)).toBeInTheDocument();
    expect(screen.getByText(/Innings 1 \(Strikers\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Innings 2 \(Warriors\)/i)).toBeInTheDocument();
    expect(screen.getByText('Save & Update Standings')).toBeInTheDocument();
  });
});

