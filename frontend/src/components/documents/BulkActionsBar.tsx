import { Trash2 } from 'lucide-react';

export function BulkActionsBar({ count, onDelete, onClear }: { count: number; onDelete: () => void; onClear: () => void }) {
  if (count === 0) return null;

  return (
    <div
      className="flex items-center justify-between rounded-lg border px-4 py-2.5 text-sm animate-fade-in"
      style={{ background: 'var(--brand-soft)', borderColor: 'var(--border)', color: 'var(--text)' }}
    >
      <span className="font-medium">{count} document{count === 1 ? '' : 's'} selected</span>
      <div className="flex items-center gap-3">
        <button type="button" onClick={onClear} className="text-xs font-medium hover:underline" style={{ color: 'var(--text-secondary)' }}>
          Clear
        </button>
        <button
          type="button"
          onClick={onDelete}
          className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition hover:opacity-90"
          style={{ background: 'var(--negative)', color: 'white' }}
        >
          <Trash2 size={13} />
          Delete selected
        </button>
      </div>
    </div>
  );
}
