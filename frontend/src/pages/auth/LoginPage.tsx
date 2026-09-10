import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { AuthCard, FormError, FormField, SubmitButton } from '../../components/auth/AuthCard';
import { getApiErrorMessage } from '../../api/client';
import { PasswordField } from '../../components/common/PasswordField';
import { useAuth } from '../../hooks/useAuth';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login({ email, password });
      const next = searchParams.get('next');
      navigate(next && next.startsWith('/') ? next : '/app', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard
      title="Sign in"
      subtitle="Welcome back — enter your details to continue."
      footer={
        <>
          Don&rsquo;t have an account?{' '}
          <Link to="/signup" className="font-medium hover:underline" style={{ color: 'var(--brand)' }}>Create one</Link>
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
        <div>
          <PasswordField
            label="Password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Link
            to="/forgot-password"
            className="mt-1.5 inline-block text-xs font-medium hover:underline"
            style={{ color: 'var(--text-secondary)' }}
          >
            Forgot your password?
          </Link>
        </div>
        <SubmitButton loading={loading}>Sign in</SubmitButton>
      </form>
    </AuthCard>
  );
}
