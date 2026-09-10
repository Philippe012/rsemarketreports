import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { useTheme } from '../../hooks/useTheme';
import type { Dataset, DocumentChart } from '../../types/report';
import { CHART_COLORS } from '../../utils/chartColors';
import { aggregateForChart } from '../../utils/genericFormat';
import { formatNumber } from '../../utils/formatters';

const PIE_COLORS = ['#146c43', '#5c5f63', '#a1590a', '#8a8d91', '#2f9e63', '#3c4044'];

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border px-3 py-2 text-xs shadow-lg" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}>
      <p className="mb-1 font-medium">{label}</p>
      <p className="tabular-nums">{formatNumber(payload[0].value, 2)}</p>
    </div>
  );
}

export function DatasetChart({ chart, dataset }: { chart: DocumentChart; dataset: Dataset }) {
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];
  const points = aggregateForChart(dataset.rows, chart.x, chart.y);
  if (points.length === 0) return null;

  return (
    <div>
      <p className="mb-2 text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{chart.title}</p>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chart.chart_type === 'line' ? (
            <LineChart data={points}>
              <CartesianGrid strokeDasharray="0" vertical={false} stroke={colors.grid} />
              <XAxis dataKey="x" tick={{ fill: colors.axis, fontSize: 11 }} axisLine={{ stroke: colors.grid }} tickLine={false} />
              <YAxis tick={{ fill: colors.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
              <Tooltip content={<ChartTooltip />} />
              <Line type="monotone" dataKey="y" stroke={colors.today} strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          ) : chart.chart_type === 'pie' ? (
            <PieChart>
              <Tooltip content={<ChartTooltip />} />
              <Pie
                data={points}
                dataKey="y"
                nameKey="x"
                cx="50%"
                cy="50%"
                outerRadius={90}
                isAnimationActive={false}
                label={(props: { name?: string }) => props.name ?? ''}
              >
                {points.map((entry, i) => (
                  <Cell key={entry.x} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          ) : (
            <BarChart data={points}>
              <CartesianGrid strokeDasharray="0" vertical={false} stroke={colors.grid} />
              <XAxis dataKey="x" tick={{ fill: colors.axis, fontSize: 11 }} axisLine={{ stroke: colors.grid }} tickLine={false} />
              <YAxis tick={{ fill: colors.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
              <Tooltip content={<ChartTooltip />} cursor={{ fill: 'transparent' }} />
              <Bar dataKey="y" fill={colors.today} radius={[4, 4, 0, 0]} maxBarSize={48} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
