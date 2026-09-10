import { Lock, ShieldCheck, UserCheck } from 'lucide-react';

import { Section } from './Section';

const PRINCIPLES = [
  {
    icon: Lock,
    title: 'Your documents, your account',
    description: 'Every upload is tied to your account. Only you can view, open or download the documents and dashboards you create.',
  },
  {
    icon: UserCheck,
    title: 'Session-based authentication',
    description: 'Sign-in is handled by the backend with secure, cookie-based sessions and CSRF protection — not a client-side check that can be bypassed.',
  },
  {
    icon: ShieldCheck,
    title: 'No data sold or shared',
    description: 'Your documents are used only to generate your dashboards and exports. They are never sold, shared, or used to train models.',
  },
];

export function Security() {
  return (
    <Section
      id="security"
      tone="subtle"
      eyebrow="Security & privacy"
      heading="Built with sound defaults, described plainly"
    >
      <div className="grid gap-4 sm:grid-cols-3">
        {PRINCIPLES.map((principle) => (
          <div key={principle.title} className="rounded-lg border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <div className="mb-3.5 flex h-9 w-9 items-center justify-center rounded-md" style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}>
              <principle.icon size={17} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{principle.title}</p>
            <p className="mt-1.5 text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{principle.description}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
