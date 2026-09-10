import { ChevronDown, FileText } from 'lucide-react';
import { useState } from 'react';

import type { DocumentSection } from '../../types/report';
import { Card } from '../common/Card';

const PREVIEW_LENGTH = 220;

function SectionItem({ section }: { section: DocumentSection }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = section.content.length > PREVIEW_LENGTH;
  const shown = expanded || !isLong ? section.content : `${section.content.slice(0, PREVIEW_LENGTH)}…`;

  return (
    <div className="border-b py-3 last:border-b-0" style={{ borderColor: 'var(--border)' }}>
      {section.title && (
        <p className="mb-1 text-sm font-semibold" style={{ color: 'var(--text)' }}>
          {section.title}
        </p>
      )}
      <p className="whitespace-pre-line text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
        {shown}
      </p>
      {isLong && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium transition hover:opacity-75"
          style={{ color: 'var(--brand)' }}
        >
          {expanded ? 'Show less' : 'Read more'}
          <ChevronDown size={12} style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }} />
        </button>
      )}
    </div>
  );
}

/** The raw extracted text, as-is — lets a user verify what the platform
 * actually read out of the document before trusting anything derived from it. */
export function SectionsList({ sections }: { sections: DocumentSection[] }) {
  if (sections.length === 0) return null;

  return (
    <Card
      title="Source"
      subtitle={`${sections.length} section${sections.length === 1 ? '' : 's'} extracted from the document`}
      icon={<FileText size={16} />}
    >
      <div>
        {sections.map((section, i) => (
          <SectionItem key={i} section={section} />
        ))}
      </div>
    </Card>
  );
}
