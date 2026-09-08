import type { ReactNode } from 'react';

interface KpiCardProps {
  label: string;
  value: string;
  sublabel?: ReactNode;
}

export function KpiCard({ label, value, sublabel }: KpiCardProps) {
  return (
    <div
      className="rounded-lg border p-5 animate-fade-in"
      style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-sm)' }}
    >
      <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>
        {label}
      </p>
      <p className="mt-2.5 text-[26px] font-semibold leading-none tabular-nums tracking-tight" style={{ color: 'var(--text)' }}>
        {value}
      </p>
      {sublabel && <div className="mt-2 text-xs" style={{ color: 'var(--text-secondary)' }}>{sublabel}</div>}
    </div>
  );
}
