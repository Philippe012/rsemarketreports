import { ArrowRight } from 'lucide-react';
import { Bar, BarChart, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { Badge } from '../common/Badge';
import { useTheme } from '../../hooks/useTheme';
import { CHART_COLORS } from '../../utils/chartColors';

const SAMPLE_BARS = [
  { x: 'W1', y: 62 }, { x: 'W2', y: 74 }, { x: 'W3', y: 58 }, { x: 'W4', y: 91 },
  { x: 'W5', y: 84 }, { x: 'W6', y: 102 }, { x: 'W7', y: 96 },
];

export function Hero() {
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];

  return (
    <section className="relative overflow-hidden" style={{ background: 'var(--bg)' }}>
      <div className="hero-backdrop" aria-hidden="true" />
    
      <div className="relative z-10 mx-auto grid max-w-[1400px] gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-[1.1fr_1fr] lg:items-center lg:px-8 lg:py-28">
        <div>
          <Badge tone="neutral">Document intelligence platform</Badge>
          <h1
            className="mt-5 text-[34px] font-semibold leading-[1.15] tracking-tight sm:text-[44px]"
            style={{ color: 'var(--text)' }}
          >
            Turn business documents into trusted data.
          </h1>
          <p className="mt-5 max-w-xl text-[16px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            Upload a PDF, Excel, Word, CSV or TXT file. Rebadata extracts the text and tables,
            validates every figure against its source, and builds structured datasets, KPIs and
            charts automatically, with nothing invented. Review what needs a second look, then
            export to Excel, CSV or JSON, or pull it in through the API.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/signup"
              className="inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold transition hover:opacity-90"
              style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
            >
              Get started free
              <ArrowRight size={16} />
            </Link>
            
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center gap-2 rounded-lg border px-5 py-3 text-sm font-medium transition hover:opacity-80"
              style={{ borderColor: 'var(--border-strong)', color: 'var(--text)' }}
            >
              See how it works
            </a>
          </div>
          <p className="mt-5 text-xs" style={{ color: 'var(--text-muted)' }}>
            No credit card required · PDF, Excel, Word, CSV and TXT supported
          </p>
        </div>

        {/* Real product preview — a representative, labeled mock of the dashboard, not live data. */}
        <div
          className="animate-fade-in overflow-hidden rounded-xl border"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-lg)' }}
        >
          <div className="flex items-center justify-between border-b px-5 py-3.5" style={{ borderColor: 'var(--border)' }}>
            <div>
              <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Q3 Sales Report</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Excel · Processed</p>
            </div>
            <span
              className="rounded-full px-2.5 py-1 text-sm font-semibold uppercase tracking-wide"
              style={{ background: 'var(--neutral-chip-soft)', color: 'var(--neutral-chip)' }}
            >
              Preview
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 p-5">
            <div className="rounded-lg border p-3.5" style={{ borderColor: 'var(--border)' }}>
              <p className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Revenue</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums" style={{ color: 'var(--text)' }}>$4.82M</p>
              <p className="mt-1 text-xs font-medium" style={{ color: 'var(--positive)' }}>+12.4%</p>
            </div>
            <div className="rounded-lg border p-3.5" style={{ borderColor: 'var(--border)' }}>
              <p className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Orders</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums" style={{ color: 'var(--text)' }}>2,318</p>
              <p className="mt-1 text-xs font-medium" style={{ color: 'var(--positive)' }}>+6.1%</p>
            </div>
          </div>

          <div className="h-28 px-5 pb-5">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={SAMPLE_BARS}>
                <Bar dataKey="y" fill={colors.today} radius={[3, 3, 0, 0]} maxBarSize={22} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

    </section>
  );
}