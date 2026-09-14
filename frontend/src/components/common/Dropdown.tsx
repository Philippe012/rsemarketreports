import { ChevronDown } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

type DropdownOption = {
  value: string;
  label: string;
};

type DropdownProps = {
  value: string;
  onChange: (value: string) => void;
  options: DropdownOption[];
  label: string;
  placeholder?: string;
  className?: string;
  menuPlacement?: 'down' | 'up';
};

export function Dropdown({
  value,
  onChange,
  options,
  label,
  placeholder = 'Select',
  className = '',
  menuPlacement = 'down',
}: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const selectedOption = options.find((option) => option.value === value) ?? {
    value: '',
    label: placeholder,
  };

  return (
    <div ref={ref} className={`relative z-30 ${className}`}>
      <span className="sr-only">{label}</span>

      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((isOpen) => !isOpen)}
        className="flex h-11 w-full items-center justify-between gap-3 rounded-xl border px-4 text-sm font-medium shadow-sm transition hover:border-(--border-strong) focus:outline-none"
        style={{
          borderColor: 'var(--border)',
          background: 'var(--surface)',
          color: 'var(--text)',
        }}
      >
        <span className="truncate">{selectedOption.label}</span>

        <ChevronDown
          size={15}
          className={`shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          style={{ color: 'var(--text-muted)' }}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className={`absolute left-0 z-50 w-full max-h-64 overflow-y-auto overflow-x-hidden rounded-xl border shadow-lg ${
            menuPlacement === 'up' ? 'bottom-full mb-2' : 'top-full mt-2'
          }`}
          
          style={{
            borderColor: 'var(--border)',
            background: 'var(--surface)',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          {options.map((option) => {
            const active = option.value === value;

            return (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={active}
                onClick={() => {
                  onChange(option.value);
                  setOpen(false);
                }}
                className="flex w-full items-center justify-between px-3 py-2.5 text-left text-sm transition hover:bg-(--surface-hover)"
                style={{
                  color: active ? 'var(--brand)' : 'var(--text)',
                  background: active ? 'var(--brand-soft)' : 'transparent',
                }}
              >
                <span>{option.label}</span>

                {active && (
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: 'var(--brand)' }}
                  />
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}