import { BarChart3 } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useTheme } from '../../hooks/useTheme';
import type { Equity } from '../../types/report';
import { CHART_COLORS } from '../../utils/chartColors';
import { formatNumber } from '../../utils/formatters';
import { Card } from '../common/Card';

const POSITIVE = { light: '#146c43', dark: '#34c47a' } as const;
const NEGATIVE = { light: '#b3261e', dark: '#e5534b' } as const;

function ChangeTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border px-3 py-2 text-xs shadow-lg" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}>
      <p className="mb-1 font-medium">{label}</p>
      <p className="tabular-nums">{formatNumber(payload[0].value, 2)}</p>
    </div>
  );
}

export function MarketAnalyticsSection({ equities }: { equities: Equity[] }) {
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];
  const posColor = POSITIVE[theme];
  const negColor = NEGATIVE[theme];

  const movers = equities
    .filter((e) => e.change !== null && e.change !== 0)
    .sort((a, b) => Math.abs(b.change ?? 0) - Math.abs(a.change ?? 0))
    .slice(0, 8)
    .map((e) => ({ name: e.ticker, value: e.change ?? 0 }));

  const activity = equities
    .filter((e) => e.volume !== null && e.volume > 0)
    .sort((a, b) => (b.volume ?? 0) - (a.volume ?? 0))
    .slice(0, 8)
    .map((e) => ({ name: e.ticker, value: e.volume ?? 0 }));

  if (movers.length === 0 && activity.length === 0) return null;

  return (
    <section>
      <div className="mb-3">
        <h2 className="text-[15px] font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Market analytics</h2>
        <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>Movers and activity from today's session</p>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        {movers.length > 0 && (
          <Card title="Gainers &amp; losers" subtitle="Price change by ticker" icon={<BarChart3 size={16} />}>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={movers}>
                  <CartesianGrid strokeDasharray="0" vertical={false} stroke={colors.grid} />
                  <XAxis dataKey="name" tick={{ fill: colors.axis, fontSize: 11 }} axisLine={{ stroke: colors.grid }} tickLine={false} />
                  <YAxis tick={{ fill: colors.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
                  <Tooltip content={<ChangeTooltip />} cursor={{ fill: 'transparent' }} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={40}>
                    {movers.map((m) => (
                      <Cell key={m.name} fill={m.value >= 0 ? posColor : negColor} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        )}

        {activity.length > 0 && (
          <Card title="Most active" subtitle="Shares traded by ticker" icon={<BarChart3 size={16} />}>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activity}>
                  <CartesianGrid strokeDasharray="0" vertical={false} stroke={colors.grid} />
                  <XAxis dataKey="name" tick={{ fill: colors.axis, fontSize: 11 }} axisLine={{ stroke: colors.grid }} tickLine={false} />
                  <YAxis tick={{ fill: colors.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
                  <Tooltip content={<ChangeTooltip />} cursor={{ fill: 'transparent' }} />
                  <Bar dataKey="value" fill={colors.today} radius={[4, 4, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        )}
      </div>
    </section>
  );
}
