import { CheckCircle2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { confirmPasswordReset } from '../../api/auth';
import { AuthCard, FormError, SubmitButton } from '../../components/auth/AuthCard';
import { getApiErrorMessage } from '../../api/client';
import { PasswordField } from '../../components/common/PasswordField';

export function ResetPasswordPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!uid || !token) return;
    setError(null);
    setLoading(true);
    try {
      await confirmPasswordReset({ uid, token, new_password: password, new_password_confirm: passwordConfirm });
      setDone(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (!uid || !token) {
    return (
      <AuthCard title="Invalid reset link">
        <FormError message="This password reset link is malformed. Please request a new one." />
        <Link to="/forgot-password" className="mt-4 inline-block text-sm font-medium hover:underline" style={{ color: 'var(--brand)' }}>
          Request a new link
        </Link>
      </AuthCard>
    );
  }

  if (done) {
    return (
      <AuthCard title="Password reset">
        <div className="flex flex-col items-center gap-3 py-2 text-center">
          <CheckCircle2 size={32} style={{ color: 'var(--positive)' }} />
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Your password has been updated.</p>
          <button
            type="button"
            onClick={() => navigate('/login', { replace: true })}
            className="mt-2 rounded-lg px-4 py-2 text-sm font-semibold"
            style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
          >
            Continue to sign in
          </button>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard title="Choose a new password">
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <PasswordField
          label="New password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <PasswordField
          label="Confirm new password"
          autoComplete="new-password"
          required
          minLength={8}
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
        />
        <SubmitButton loading={loading}>Reset password</SubmitButton>
      </form>
    </AuthCard>
  );
}
