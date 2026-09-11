import { AlertTriangle, ChevronDown } from 'lucide-react';
import { useState } from 'react';

export function WarningsPanel({ warnings }: { warnings: string[] }) {
  const [expanded, setExpanded] = useState(false);
  if (warnings.length === 0) return null;

  return (
    <div
      className="overflow-hidden rounded-lg border animate-fade-in"
      style={{ borderColor: 'color-mix(in srgb, var(--warning) 35%, var(--border))', background: 'var(--warning-soft)' }}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <span className="flex items-center gap-2.5">
          <AlertTriangle size={15} style={{ color: 'var(--warning)' }} />
          <span>
            <span className="block text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--warning)' }}>
              Data quality
            </span>
            <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>
              {warnings.length} {warnings.length === 1 ? 'issue requires' : 'issues require'} review
            </span>
          </span>
        </span>
        <ChevronDown
          size={16}
          style={{ color: 'var(--warning)', transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
        />
      </button>
      {expanded && (
        <ul className="space-y-1.5 border-t px-4 py-3 text-sm" style={{ borderColor: 'var(--warning)', color: 'var(--text)' }}>
          {warnings.map((warning, i) => (
            <li key={i} className="flex gap-2">
              <span style={{ color: 'var(--warning)' }}>•</span>
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
