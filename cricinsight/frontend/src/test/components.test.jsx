import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import QueryInput from '../components/QueryInput';
import StatCards from '../components/StatCards';
import QueryScopeBadge from '../components/QueryScopeBadge';
import InsightPanel from '../components/InsightPanel';

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
});

