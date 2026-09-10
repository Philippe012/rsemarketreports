import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { AuthCard, FormError, FormField, SubmitButton } from '../../components/auth/AuthCard';
import { getApiErrorMessage } from '../../api/client';
import { PasswordField } from '../../components/common/PasswordField';
import { useAuth } from '../../hooks/useAuth';

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup({ email, password, password_confirm: passwordConfirm });
      navigate('/app', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="Create your account"
      subtitle="Start turning documents into dashboards in minutes."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--brand)' }}>Sign in</Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <FormField
          label="Email address"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <PasswordField
          label="Password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <PasswordField
          label="Confirm password"
          autoComplete="new-password"
          required
          minLength={8}
          value={passwordConfirm}
          onChange={(e) => setPasswordConfirm(e.target.value)}
        />
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          Use at least 8 characters. Avoid common passwords or ones too similar to your email.
        </p>
        <SubmitButton loading={loading}>Create account</SubmitButton>
      </form>
    </AuthCard>
  );
}
