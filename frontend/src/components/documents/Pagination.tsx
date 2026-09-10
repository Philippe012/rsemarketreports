import { ChevronLeft, ChevronRight } from 'lucide-react';

export function Pagination({
  page,
  totalPages,
  count,
  onChange,
}: {
  page: number;
  totalPages: number;
  count: number;
  onChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between px-1 py-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
      <span>{count} document{count === 1 ? '' : 's'} · page {page} of {totalPages}</span>
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="flex h-7 w-7 items-center justify-center rounded-md border transition hover:opacity-80 disabled:opacity-40"
          style={{ borderColor: 'var(--border)' }}
          aria-label="Previous page"
        >
          <ChevronLeft size={14} />
        </button>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="flex h-7 w-7 items-center justify-center rounded-md border transition hover:opacity-80 disabled:opacity-40"
          style={{ borderColor: 'var(--border)' }}
          aria-label="Next page"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}
