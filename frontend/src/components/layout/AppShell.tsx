import { LayoutDashboard, LogOut, Menu, Settings, ShieldCheck, UploadCloud, User as UserIcon, X } from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import logoIcon from '../../assets/logo-icon-square.png';
import { ThemeToggle } from '../common/ThemeToggle';
import { useAuth } from '../../hooks/useAuth';

const NAV_ITEMS = [
  { to: '/app', label: 'Home', icon: UploadCloud, end: true },
  { to: '/app/documents', label: 'Documents', icon: LayoutDashboard, end: false },
  { to: '/app/settings', label: 'Settings', icon: Settings, end: false },
];

const ADMIN_NAV_ITEM = { to: '/app/admin/documents', label: 'Admin', icon: ShieldCheck, end: false };

function navLinkStyle(isActive: boolean) {
  return {
    color: isActive ? 'var(--text)' : 'var(--text-secondary)',
    background: isActive ? 'var(--bg-subtle)' : 'transparent',
  };
}

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navItems = user?.is_staff ? [...NAV_ITEMS, ADMIN_NAV_ITEM] : NAV_ITEMS;

  const handleLogout = async () => {
    setMenuOpen(false);
    // Navigate away from the protected /app tree BEFORE clearing the auth
    // state: otherwise ProtectedRoute (still mounted for a tick) reacts to
    // status flipping to 'anonymous' and races this navigation to /login,
    // occasionally winning and stranding the user there instead of on the
    // landing page.
    navigate('/', { replace: true });
    await logout();
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <header
        className="sticky top-0 z-30 border-b backdrop-blur-md"
        style={{ background: 'color-mix(in srgb, var(--surface) 88%, transparent)', borderColor: 'var(--border)' }}
      >
        <div className="mx-auto flex max-w-[1400px] items-center gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-ml-1.5 flex h-9 w-9 items-center justify-center rounded-lg lg:hidden"
            style={{ color: 'var(--text)' }}
            onClick={() => setDrawerOpen((v) => !v)}
            aria-label="Toggle navigation"
          >
            {drawerOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <NavLink to="/app" className="flex items-center gap-2.5">
            <img src={logoIcon} alt="Datapoint" className="h-8 w-8 shrink-0 rounded-lg object-contain" />
            <span className="hidden text-[15px] font-semibold tracking-tight sm:inline" style={{ color: 'var(--text)' }}>
              Datapoint
            </span>
          </NavLink>

          <nav className="ml-4 hidden items-center gap-1 lg:flex" aria-label="Primary">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition"
                style={({ isActive }) => navLinkStyle(isActive)}
              >
                <item.icon size={15} />
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />

            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                className="flex h-9 items-center gap-2 rounded-full border pl-1 pr-3 transition hover:opacity-80"
                style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
              >
                <span
                  className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold"
                  style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}
                >
                  {(user?.email ?? '?').charAt(0).toUpperCase()}
                </span>
                <span className="hidden max-w-[10rem] truncate text-sm font-medium sm:inline" style={{ color: 'var(--text)' }}>
                  {user?.email}
                </span>
              </button>

              {menuOpen && (
                <>
                  <button
                    type="button"
                    className="fixed inset-0 z-40 cursor-default"
                    aria-label="Close menu"
                    onClick={() => setMenuOpen(false)}
                  />
                  <div
                    className="absolute right-0 z-50 mt-2 w-52 overflow-hidden rounded-lg border py-1 animate-fade-in"
                    style={{ background: 'var(--surface)', borderColor: 'var(--border)', boxShadow: 'var(--shadow-md)' }}
                  >
                    <div className="border-b px-3.5 py-2.5" style={{ borderColor: 'var(--border)' }}>
                      <p className="truncate text-sm font-medium" style={{ color: 'var(--text)' }}>{user?.email}</p>
                    </div>
                    <NavLink
                      to="/app/settings"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2.5 text-sm transition hover:opacity-80"
                      style={{ color: 'var(--text)' }}
                    >
                      <UserIcon size={15} /> Account settings
                    </NavLink>
                    <button
                      type="button"
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-sm transition hover:opacity-80"
                      style={{ color: 'var(--negative)' }}
                    >
                      <LogOut size={15} /> Log out
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {drawerOpen && (
          <nav className="border-t px-4 py-2 lg:hidden" style={{ borderColor: 'var(--border)' }} aria-label="Primary">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setDrawerOpen(false)}
                className="flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition"
                style={({ isActive }) => navLinkStyle(isActive)}
              >
                <item.icon size={16} />
                {item.label}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}
