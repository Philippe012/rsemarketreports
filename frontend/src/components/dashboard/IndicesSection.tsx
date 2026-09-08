import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useTheme } from '../../hooks/useTheme';
import type { MarketIndex } from '../../types/report';
import { CHART_COLORS } from '../../utils/chartColors';
import { formatNumber, formatPercent, formatSignedNumber, trendDirection } from '../../utils/formatters';
import { ChangeBadge } from '../common/Badge';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';

interface TooltipPayloadEntry {
  dataKey: string;
  name: string;
  value: number;
  color: string;
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadEntry[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-md border px-3 py-2 text-xs shadow-lg"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}
    >
      <p className="mb-1 font-medium">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="flex items-center gap-1.5 tabular-nums">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: entry.color }} />
          {entry.name}: {formatNumber(entry.value, 2)}
        </p>
      ))}
    </div>
  );
}

export function IndicesSection({ indices }: { indices: MarketIndex[] }) {
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];

  if (indices.length === 0) {
    return (
      <Card title="Market indices" subtitle="RSI, ALSI and other published indices">
        <EmptyState message="No index data (RSI/ALSI) was found in this report." />
      </Card>
    );
  }

  const hasPreviousToday = indices.some((idx) => idx.previous !== null && idx.today !== null);
  const chartData = indices.map((idx) => ({
    name: idx.name,
    previous: idx.previous ?? idx.closing,
    today: idx.today ?? idx.closing,
  }));

  return (
    <Card title="Market indices" subtitle="RSI, ALSI and other published indices">
      <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-1">
          {indices.map((idx) => (
            <div
              key={idx.name}
              className="rounded-lg border p-4"
              style={{ borderColor: 'var(--border)', background: 'var(--bg-subtle)' }}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{idx.name}</p>
                {idx.percent_change !== null && (
                  <ChangeBadge value={idx.percent_change} formatted={formatPercent(idx.percent_change)} />
                )}
              </div>
              <p className="mt-2 text-2xl font-semibold tabular-nums tracking-tight" style={{ color: 'var(--text)' }}>
                {formatNumber(idx.closing, 2)}
              </p>
              {idx.previous !== null && (
                <p className="mt-1 text-xs tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                  Previous: {formatNumber(idx.previous, 2)}
                  {idx.points_change !== null && (
                    <span
                      className="ml-1.5"
                      style={{
                        color:
                          trendDirection(idx.points_change) === 'down'
                            ? 'var(--negative)'
                            : trendDirection(idx.points_change) === 'up'
                              ? 'var(--positive)'
                              : 'var(--text-secondary)',
                      }}
                    >
                      ({formatSignedNumber(idx.points_change, 2)} pts)
                    </span>
                  )}
                </p>
              )}
            </div>
          ))}
        </div>

        {hasPreviousToday && (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} barCategoryGap="28%" barGap={4}>
                <CartesianGrid strokeDasharray="0" vertical={false} stroke={colors.grid} />
                <XAxis dataKey="name" tick={{ fill: colors.axis, fontSize: 12 }} axisLine={{ stroke: colors.grid }} tickLine={false} />
                <YAxis tick={{ fill: colors.axis, fontSize: 12 }} axisLine={false} tickLine={false} width={48} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: 'transparent' }} />
                <Legend wrapperStyle={{ fontSize: 12, color: colors.text }} iconType="circle" iconSize={8} />
                <Bar dataKey="previous" name="Previous" fill={colors.previous} radius={[4, 4, 0, 0]} maxBarSize={24} />
                <Bar dataKey="today" name="Today" fill={colors.today} radius={[4, 4, 0, 0]} maxBarSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </Card>
  );
}
