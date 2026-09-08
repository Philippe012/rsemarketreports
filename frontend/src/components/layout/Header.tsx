import { UploadCloud } from 'lucide-react';

import logoIcon from '../../assets/logo-icon-square.png';
import { ThemeToggle } from '../common/ThemeToggle';

export function Header({ showNewUpload, onNewUpload }: { showNewUpload: boolean; onNewUpload: () => void }) {
  return (
    <header
      className="sticky top-0 z-30 border-b backdrop-blur-md"
      style={{ background: 'color-mix(in srgb, var(--surface) 88%, transparent)', borderColor: 'var(--border)' }}
    >
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <img src={logoIcon} alt="RSE Report Dashboard" className="h-9 w-9 shrink-0 rounded-lg object-contain" />
          <div>
            <p className="text-[15px] font-semibold leading-tight tracking-tight" style={{ color: 'var(--text)' }}>
              RSE Market Reports
            </p>
            <p className="text-[11px] leading-tight" style={{ color: 'var(--text-secondary)' }}>
              Document-to-dashboard for Rwanda Stock Exchange reports
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {showNewUpload && (
            <button
              type="button"
              onClick={onNewUpload}
              className="inline-flex items-center gap-2 rounded-lg border px-3.5 py-2 text-sm font-medium transition hover:opacity-80"
              style={{ borderColor: 'var(--border)', color: 'var(--text)', background: 'var(--surface)' }}
            >
              <UploadCloud size={15} />
              <span className="hidden sm:inline">New report</span>
            </button>
          )}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
