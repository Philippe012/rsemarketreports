import { Inbox } from 'lucide-react';
import type { ReactNode } from 'react';

export function EmptyState({
  message = 'No data available in this report for this section.',
  icon,
}: {
  message?: string;
  icon?: ReactNode;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-6 py-10 text-center"
      style={{ borderColor: 'var(--border-strong)', color: 'var(--text-muted)' }}
    >
      {icon ?? <Inbox size={26} strokeWidth={1.5} />}
      <p className="max-w-sm text-sm">{message}</p>
    </div>
  );
}
