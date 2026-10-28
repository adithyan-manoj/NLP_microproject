import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { BarChart3, LineChart as LineChartIcon, Info } from 'lucide-react';

const COLORS = ['#10b981', '#38bdf8', '#f59e0b', '#ec4899', '#a855f7'];

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const dataPoint = payload[0]?.payload;
    return (
      <div className="bg-slate-900/95 border border-slate-700/80 p-3 rounded-xl shadow-2xl backdrop-blur text-xs">
        <div className="font-semibold text-slate-200 mb-1 border-b border-slate-800 pb-1 flex items-center justify-between gap-4">
          <span>{label}</span>
          {dataPoint?.date && <span className="text-slate-400 font-normal">{dataPoint.date}</span>}
        </div>
        {payload.map((entry, index) => (
          <div key={`item-${index}`} className="flex items-center justify-between gap-4 py-0.5" style={{ color: entry.color }}>
            <span className="font-medium">{entry.name}:</span>
            <span className="font-bold text-slate-100">{entry.value} runs</span>
          </div>
        ))}
        {dataPoint?.opponent && (
          <div className="mt-1 pt-1 border-t border-slate-800/80 text-[10px] text-slate-400">
            vs {dataPoint.opponent} {dataPoint.balls ? `(${dataPoint.balls} balls)` : ''}
          </div>
        )}
      </div>
    );
  }
  return null;
}

export default function ChartRenderer({ chartSpec }) {
  if (!chartSpec || !chartSpec.series || chartSpec.series.length === 0) {
    return null;
  }

  const defaultType = chartSpec.chart_type === 'bar' ? 'bar' : 'line';
  const [viewType, setViewType] = useState(defaultType);

  // Transform backend chart format to recharts format
  // Series is: [{ name: "Virat Kohli", data: [{ x: "Inn 1", y: 74, ... }] }, ...]
  const seriesList = chartSpec.series;
  const isComparison = seriesList.length > 1;

  // Build unified points array keyed by x
  const xLabels = [];
  seriesList.forEach((s) => {
    s.data?.forEach((pt) => {
      if (!xLabels.includes(pt.x)) {
        xLabels.push(pt.x);
      }
    });
  });

  const chartData = xLabels.map((x) => {
    const row = { x };
    seriesList.forEach((s) => {
      const match = s.data?.find((pt) => pt.x === x);
      if (match) {
        row[s.name] = match.y;
        if (match.opponent) row.opponent = match.opponent;
        if (match.date) row.date = match.date;
        if (match.balls) row.balls = match.balls;
      }
    });
    return row;
  });

  return (
    <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-5 shadow-xl backdrop-blur flex flex-col gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h3 className="text-base font-semibold text-slate-100 tracking-tight">
            {chartSpec.title || "Innings Performance Progression"}
          </h3>
          <p className="text-xs text-slate-400">
            {chartSpec.subtitle || "Chronological cricket scoring records"}
          </p>
        </div>

        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setViewType('line')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg transition font-medium ${
              viewType === 'line'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LineChartIcon className="w-3.5 h-3.5" /> Line
          </button>
          <button
            type="button"
            onClick={() => setViewType('bar')}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg transition font-medium ${
              viewType === 'bar'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" /> Bar
          </button>
        </div>
      </div>

      <div className="w-full h-72 md:h-80">
        <ResponsiveContainer width="100%" height="100%">
          {viewType === 'line' ? (
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
              <XAxis dataKey="x" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              {isComparison && <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />}
              {seriesList.map((s, idx) => (
                <Line
                  key={s.name}
                  type="monotone"
                  dataKey={s.name}
                  stroke={COLORS[idx % COLORS.length]}
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: COLORS[idx % COLORS.length], strokeWidth: 2, stroke: '#0f172a' }}
                  activeDot={{ r: 6, stroke: '#f8fafc', strokeWidth: 2 }}
                />
              ))}
            </LineChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} vertical={false} />
              <XAxis dataKey="x" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<CustomTooltip />} />
              {isComparison && <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />}
              {seriesList.map((s, idx) => (
                <Bar
                  key={s.name}
                  dataKey={s.name}
                  fill={COLORS[idx % COLORS.length]}
                  radius={[6, 6, 0, 0]}
                  maxBarSize={40}
                />
              ))}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-2 text-[11px] text-slate-500 border-t border-slate-800/80 pt-3">
        <Info className="w-3.5 h-3.5 text-slate-400" />
        <span>Grounded on actual ball-by-ball delivery records from DuckDB.</span>
      </div>
    </div>
  );
}
