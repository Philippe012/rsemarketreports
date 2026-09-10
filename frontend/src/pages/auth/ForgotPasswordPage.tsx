import { CheckCircle2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';

import { requestPasswordReset } from '../../api/auth';
import { AuthCard, FormError, FormField, SubmitButton } from '../../components/auth/AuthCard';
import { getApiErrorMessage } from '../../api/client';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await requestPasswordReset(email);
      setSent(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <AuthCard title="Check your email" footer={<Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--brand)' }}>Back to sign in</Link>}>
        <div className="flex flex-col items-center gap-3 py-2 text-center">
          <CheckCircle2 size={32} style={{ color: 'var(--positive)' }} />
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            If an account exists for <strong style={{ color: 'var(--text)' }}>{email}</strong>, a reset link is on its way. It may take a minute to arrive.
          </p>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Reset your password"
      subtitle="Enter your email and we'll send you a reset link."
      footer={<Link to="/login" className="font-medium hover:underline" style={{ color: 'var(--brand)' }}>Back to sign in</Link>}
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
        <SubmitButton loading={loading}>Send reset link</SubmitButton>
      </form>
    </AuthCard>
  );
}
