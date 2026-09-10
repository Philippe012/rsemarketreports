import { Menu, X } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import logoIcon from '../../assets/logo-icon-square.png';
import { ThemeToggle } from '../common/ThemeToggle';

const LINKS = [
  { href: '#how-it-works', label: 'How it works' },
  { href: '#capabilities', label: 'Capabilities' },
  { href: '#use-cases', label: 'Use cases' },
  { href: '#security', label: 'Security' },
];

export function LandingNav() {
  const [open, setOpen] = useState(false);

  return (
    <header
      className="sticky top-0 z-30 border-b backdrop-blur-md"
      style={{ background: 'color-mix(in srgb, var(--surface) 88%, transparent)', borderColor: 'var(--border)' }}
    >
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <img src={logoIcon} alt="Datapoint" className="h-9 w-9 shrink-0 rounded-lg object-contain" />
          <span className="text-[15px] font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Datapoint</span>
        </Link>

        <nav className="hidden items-center gap-7 lg:flex" aria-label="Section">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium transition hover:opacity-70"
              style={{ color: 'var(--text-secondary)' }}
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2.5">
          <div className="hidden items-center gap-2.5 sm:flex">
            <ThemeToggle />
            <Link
              to="/login"
              className="rounded-lg px-3.5 py-2 text-sm font-medium transition hover:opacity-80"
              style={{ color: 'var(--text)' }}
            >
              Sign in
            </Link>
            <Link
              to="/signup"
              className="rounded-lg px-3.5 py-2 text-sm font-semibold transition hover:opacity-90"
              style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
            >
              Get started
            </Link>
          </div>

          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-lg sm:hidden"
            style={{ color: 'var(--text)' }}
            onClick={() => setOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t px-4 py-3 sm:hidden" style={{ borderColor: 'var(--border)' }}>
          <nav className="flex flex-col gap-1" aria-label="Section">
            {LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="rounded-lg px-2 py-2.5 text-sm font-medium"
                style={{ color: 'var(--text-secondary)' }}
              >
                {link.label}
              </a>
            ))}
          </nav>
          <div className="mt-2 flex items-center gap-2.5 border-t pt-3" style={{ borderColor: 'var(--border)' }}>
            <ThemeToggle />
            <Link to="/login" className="flex-1 rounded-lg border px-3.5 py-2 text-center text-sm font-medium" style={{ borderColor: 'var(--border)', color: 'var(--text)' }}>
              Sign in
            </Link>
            <Link to="/signup" className="flex-1 rounded-lg px-3.5 py-2 text-center text-sm font-semibold" style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}>
              Get started
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
