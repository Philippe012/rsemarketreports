import type { ReactNode } from 'react';

type Tone = 'positive' | 'negative' | 'neutral' | 'warning';

const TONE_STYLES: Record<Tone, { bg: string; fg: string }> = {
  positive: { bg: 'var(--positive-soft)', fg: 'var(--positive)' },
  negative: { bg: 'var(--negative-soft)', fg: 'var(--negative)' },
  neutral: { bg: 'var(--neutral-chip-soft)', fg: 'var(--neutral-chip)' },
  warning: { bg: 'var(--warning-soft)', fg: 'var(--warning)' },
};

export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  const style = TONE_STYLES[tone];
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium tabular-nums"
      style={{ background: style.bg, color: style.fg }}
    >
      {children}
    </span>
  );
}

export function ChangeBadge({ value, formatted }: { value: number | null | undefined; formatted: string }) {
  const tone: Tone = value === null || value === undefined || value === 0 ? 'neutral' : value > 0 ? 'positive' : 'negative';
  return <Badge tone={tone}>{formatted}</Badge>;
}
