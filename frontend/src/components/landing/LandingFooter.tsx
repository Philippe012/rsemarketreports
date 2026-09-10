import { Link } from 'react-router-dom';

import logoIcon from '../../assets/logo-icon-square.png';

export function LandingFooter() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t" style={{ borderColor: 'var(--border)', background: 'var(--bg-subtle)' }}>
      <div className="mx-auto max-w-[1400px] px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex flex-col items-center gap-2.5 sm:items-start">
            <Link to="/" className="flex items-center gap-2.5">
              <img src={logoIcon} alt="Datapoint" className="h-7 w-7 rounded-md object-contain" />
              <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Datapoint</span>
            </Link>
            <p className="max-w-xs text-center text-xs leading-relaxed sm:text-left" style={{ color: 'var(--text-muted)' }}>
              A universal document-to-dashboard platform. RSE market reports are one specialized profile.
            </p>
          </div>

          <div className="flex gap-10 text-sm">
            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Product</span>
              <a href="#how-it-works" style={{ color: 'var(--text-secondary)' }} className="hover:underline">How it works</a>
              <a href="#capabilities" style={{ color: 'var(--text-secondary)' }} className="hover:underline">Capabilities</a>
              <a href="#security" style={{ color: 'var(--text-secondary)' }} className="hover:underline">Security</a>
            </div>
            <div className="flex flex-col gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Account</span>
              <Link to="/login" style={{ color: 'var(--text-secondary)' }} className="hover:underline">Sign in</Link>
              <Link to="/signup" style={{ color: 'var(--text-secondary)' }} className="hover:underline">Create account</Link>
            </div>
          </div>
        </div>

        <p className="mt-8 border-t pt-6 text-center text-xs sm:text-left" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
          © {year} Datapoint. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
