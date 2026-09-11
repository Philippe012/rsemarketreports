import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  icon?: ReactNode;
}

export function Card({ title, subtitle, actions, children, className = '', icon }: CardProps) {
  return (
    <section
      className={`rounded-lg border animate-fade-in ${className}`}
      style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-sm)' }}
    >
      {(title || actions) && (
        <div
          className="flex items-start justify-between gap-4 border-b px-5 py-4 sm:px-6"
          style={{ borderColor: 'var(--border)' }}
        >
          <div className="flex items-start gap-3">
            {icon && (
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md"
                style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}
              >
                {icon}
              </div>
            )}
            <div>
              {title && (
                <h2 className="text-base font-semibold tracking-tight" style={{ color: 'var(--text)' }}>
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="mt-0.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-5 sm:p-6">{children}</div>
    </section>
  );
}
