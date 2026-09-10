import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export function FinalCta() {
  return (
    <section className="border-t" style={{ borderColor: 'var(--border)' }}>
      <div className="mx-auto max-w-[1400px] px-4 py-16 text-center sm:px-6 sm:py-20 lg:px-8">
        <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl" style={{ color: 'var(--text)' }}>
          Turn your next document into a dashboard.
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-[15px]" style={{ color: 'var(--text-secondary)' }}>
          Free to start. Upload your first PDF, Excel, Word, CSV or TXT file in under a minute.
        </p>
        <Link
          to="/signup"
          className="mt-7 inline-flex items-center gap-2 rounded-lg px-6 py-3 text-sm font-semibold transition hover:opacity-90"
          style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
        >
          Get started free
          <ArrowRight size={16} />
        </Link>
      </div>
    </section>
  );
}
