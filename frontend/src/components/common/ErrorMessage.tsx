import { AlertTriangle, RotateCcw } from 'lucide-react';

export function ErrorMessage({
  title = 'Something went wrong',
  message,
  onRetry,
}: {
  title?: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      className="flex flex-col items-center gap-4 rounded-lg border px-8 py-12 text-center animate-fade-in"
      style={{ background: 'var(--negative-soft)', borderColor: 'color-mix(in srgb, var(--negative) 35%, var(--border))' }}
    >
      <div
        className="flex h-12 w-12 items-center justify-center rounded-full"
        style={{ background: 'var(--surface)', color: 'var(--negative)' }}
      >
        <AlertTriangle size={22} />
      </div>
      <div>
        <h3 className="text-base font-semibold" style={{ color: 'var(--text)' }}>
          {title}
        </h3>
        <p className="mx-auto mt-1.5 max-w-md text-sm" style={{ color: 'var(--text-secondary)' }}>
          {message}
        </p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition hover:opacity-90"
          style={{ background: 'var(--negative)' }}
        >
          <RotateCcw size={15} />
          Try another file
        </button>
      )}
    </div>
  );
}
