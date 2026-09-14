import { CartesianGrid, Line, LineChart, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { Section } from './Section';
import { Card } from '../common/Card';
import { TableShell, TD, TH } from '../dashboard/TableShell';
import { useTheme } from '../../hooks/useTheme';
import { CHART_COLORS } from '../../utils/chartColors';

const TREND = [
  { x: 'Jan', y: 214.1 }, { x: 'Feb', y: 219.6 }, { x: 'Mar', y: 211.8 }, { x: 'Apr', y: 228.4 },
  { x: 'May', y: 231.0 }, { x: 'Jun', y: 226.7 }, { x: 'Jul', y: 238.9 },
];

const ROWS = [
  { name: 'Warehouse A', closing: 660, change: '+1.2%' },
  { name: 'Warehouse B', closing: 515, change: '-0.4%' },
  { name: 'Warehouse C', closing: 1200, change: '0.0%' },
  { name: 'Warehouse D', closing: 500, change: '+0.8%' },
];

export function DashboardPreview() {
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];

  return (
    <Section
      eyebrow="Dashboard"
      heading="A dashboard shaped by your data, not a fixed template"
      subheading="Charts and tables are generated from what's actually in the document illustrative sample shown below."
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_1fr]">
        <Card title="Inventory trend" subtitle="7-month stock level">
          <div className="min-w-0">
            <div className="h-56 w-full sm:h-64 md:h-72 lg:h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={TREND} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="0" vertical={false} stroke={colors.grid} />
                  <XAxis
                    dataKey="x"
                    tick={{ fill: colors.axis, fontSize: 11 }}
                    axisLine={{ stroke: colors.grid }}
                    tickLine={false}
                    interval="preserveStartEnd"
                    minTickGap={12}
                  />
                  <YAxis
                    tick={{ fill: colors.axis, fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={38}
                    domain={['dataMin - 5', 'dataMax + 5']}
                  />
                  <Line type="monotone" dataKey="y" stroke={colors.today} strokeWidth={2} dot={{ r: 3 }} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>

        <Card title="Top locations" subtitle="Units on hand & change">
          <div className="-mx-1 overflow-x-auto px-1">
            <TableShell>
              <thead>
                <tr>
                  <TH>Location</TH>
                  <TH align="right">Units</TH>
                  <TH align="right">Change</TH>
                </tr>
              </thead>
              <tbody>
                {ROWS.map((row) => (
                  <tr key={row.name}>
                    <TD style={{ color: 'var(--text)' }} className="whitespace-nowrap font-medium">{row.name}</TD>
                    <TD align="right" className="whitespace-nowrap">{row.closing.toLocaleString()}</TD>
                    <TD
                      align="right"
                      className="whitespace-nowrap"
                      style={{ color: row.change.startsWith('+') ? 'var(--positive)' : row.change.startsWith('-') ? 'var(--negative)' : undefined }}
                    >
                      {row.change}
                    </TD>
                  </tr>
                ))}
              </tbody>
            </TableShell>
          </div>
        </Card>
      </div>
    </Section>
  );
}