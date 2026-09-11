import type { ReactNode } from 'react';

export function TableShell({ children }: { children: ReactNode }) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[640px] border-collapse text-sm">{children}</table>
      <style>{`
        .table-row-hover:hover { background: var(--surface-hover); }
      `}</style>
    </div>
  );
}

export function TH({ children, align = 'left' }: { children: ReactNode; align?: 'left' | 'right' | 'center' }) {
  return (
    <th
      className={`sticky top-0 whitespace-nowrap border-b px-4 py-2.5 text-sm font-semibold uppercase tracking-wide ${
        align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : 'text-left'
      }`}
      style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--surface)' }}
    >
      {children}
    </th>
  );
}

export function TD({
  children,
  align = 'left',
  className = '',
  style,
}: {
  children: ReactNode;
  align?: 'left' | 'right' | 'center';
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <td
      className={`whitespace-nowrap border-b px-4 py-2.5 tabular-nums ${
        align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : 'text-left'
      } ${className}`}
      style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', ...style }}
    >
      {children}
    </td>
  );
}
