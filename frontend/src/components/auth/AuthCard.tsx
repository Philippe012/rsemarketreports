import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import logoIcon from '../../assets/logo-icon-square.png';
import { Spinner } from '../common/Spinner';

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-12" style={{ background: 'var(--bg)' }}>
      <Link to="/" className="mb-8 flex items-center gap-2.5">
        <img src={logoIcon} alt="Datapoint" className="h-9 w-9 rounded-lg object-contain" />
        <span className="text-[15px] font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Datapoint</span>
      </Link>

      <div
        className="w-full max-w-100 rounded-lg border p-7 animate-fade-in sm:p-8"
        style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-sm)' }}
      >
        <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--text)' }}>{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>{subtitle}</p>}

        <div className="mt-6">{children}</div>
      </div>

      {footer && <div className="mt-6 text-sm" style={{ color: 'var(--text-secondary)' }}>{footer}</div>}
    </div>
  );
}

export function FormField({
  label,
  ...props
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{label}</span>
      <input
        {...props}
        className="w-full rounded-lg border px-3.5 py-2.5 text-sm outline-none transition focus:ring-2"
        style={{ background: 'var(--bg-subtle)', borderColor: 'var(--border)', color: 'var(--text)' }}
      />
    </label>
  );
}

export function FormError({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      className="rounded-lg border px-3.5 py-2.5 text-sm"
      style={{ background: 'var(--negative-soft)', borderColor: 'color-mix(in srgb, var(--negative) 35%, var(--border))', color: 'var(--negative)' }}
    >
      {message}
    </div>
  );
}

export function SubmitButton({ children, loading }: { children: ReactNode; loading?: boolean }) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition hover:opacity-90 disabled:opacity-60"
      style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
    >
      {loading && <Spinner size={15} />}
      {children}
    </button>
  );
}
