import { LogOut } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { changePassword } from '../api/auth';
import { getApiErrorMessage } from '../api/client';
import { Card } from '../components/common/Card';
import { PasswordField } from '../components/common/PasswordField';
import { ThemeToggle } from '../components/common/ThemeToggle';
import { useAuth } from '../hooks/useAuth';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setLoading(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setNewPasswordConfirm('');
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    navigate('/', { replace: true });
    await logout();
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Settings</h1>
        <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>Manage your account and preferences.</p>
      </div>

      <Card title="Account">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Email</p>
            <p className="mt-1 text-sm" style={{ color: 'var(--text)' }}>{user?.email}</p>
          </div>
        </div>
      </Card>

      <Card title="Appearance" subtitle="Choose how Datapoint looks on this device.">
        <div className="flex items-center justify-between">
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Theme</p>
          <ThemeToggle />
        </div>
      </Card>

      <Card title="Change password">
        <form onSubmit={handleChangePassword} className="space-y-4">
          {error && (
            <div className="rounded-lg border px-3.5 py-2.5 text-sm" style={{ background: 'var(--negative-soft)', borderColor: 'color-mix(in srgb, var(--negative) 35%, var(--border))', color: 'var(--negative)' }}>
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-lg border px-3.5 py-2.5 text-sm" style={{ background: 'var(--positive-soft)', borderColor: 'color-mix(in srgb, var(--positive) 35%, var(--border))', color: 'var(--positive)' }}>
              Your password has been updated.
            </div>
          )}
          <PasswordField
            label="Current password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          <PasswordField
            label="New password"
            autoComplete="new-password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <PasswordField
            label="Confirm new password"
            autoComplete="new-password"
            required
            minLength={8}
            value={newPasswordConfirm}
            onChange={(e) => setNewPasswordConfirm(e.target.value)}
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg px-4 py-2.5 text-sm font-semibold transition hover:opacity-90 disabled:opacity-60"
            style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
          >
            Update password
          </button>
        </form>
      </Card>

      <button
        type="button"
        onClick={handleLogout}
        className="inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition hover:opacity-80"
        style={{ borderColor: 'var(--border)', color: 'var(--negative)', background: 'var(--surface)' }}
      >
        <LogOut size={15} />
        Log out
      </button>
    </div>
  );
}
