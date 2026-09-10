import { Eye, EyeOff } from 'lucide-react';
import { useId, useState } from 'react';

export function PasswordField({
  label,
  value,
  onChange,
  autoComplete,
  required,
  minLength,
}: {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  autoComplete?: string;
  required?: boolean;
  minLength?: number;
}) {
  const [visible, setVisible] = useState(false);
  const id = useId();

  return (
    <label className="block" htmlFor={id}>
      <span className="mb-1.5 block text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{label}</span>
      <div className="relative">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          autoComplete={autoComplete}
          required={required}
          minLength={minLength}
          value={value}
          onChange={onChange}
          className="w-full rounded-lg border py-2.5 pl-3.5 pr-10 text-sm outline-none transition focus:ring-2"
          style={{ background: 'var(--bg-subtle)', borderColor: 'var(--border)', color: 'var(--text)' }}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          tabIndex={-1}
          aria-label={visible ? 'Hide password' : 'Show password'}
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center transition hover:opacity-70"
          style={{ color: 'var(--text-muted)' }}
        >
          {visible ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </label>
  );
}
