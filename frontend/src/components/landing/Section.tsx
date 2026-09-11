import type { ReactNode } from 'react';

export function Section({
  id,
  eyebrow,
  heading,
  subheading,
  children,
  tone = 'default',
}: {
  id?: string;
  eyebrow?: string;
  heading?: string;
  subheading?: string;
  children?: ReactNode;
  tone?: 'default' | 'subtle';
}) {
  return (
    <section id={id} className="scroll-mt-20" style={tone === 'subtle' ? { background: 'var(--bg-subtle)' } : undefined}>
      <div className="mx-auto max-w-[1400px] px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        {(eyebrow || heading) && (
          <div className="mx-auto mb-10 max-w-2xl text-center">
            {eyebrow && (
              <p className="text-sm font-semibold uppercase tracking-wider" style={{ color: 'var(--brand)' }}>
                {eyebrow}
              </p>
            )}
            {heading && (
              <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl" style={{ color: 'var(--text)' }}>
                {heading}
              </h2>
            )}
            {subheading && (
              <p className="mt-3 text-[15px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                {subheading}
              </p>
            )}
          </div>
        )}
        {children}
      </div>
    </section>
  );
}
