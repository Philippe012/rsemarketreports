import { FileSearch } from 'lucide-react';

import type { DocumentEntities } from '../../types/report';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';

function ChipGroup({ label, values }: { label: string; values: string[] }) {
  if (values.length === 0) return null;
  return (
    <div>
      <p className="mb-2 text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>
        {label}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {values.map((value, i) => (
          <Badge key={i} tone="neutral">
            {value}
          </Badge>
        ))}
      </div>
    </div>
  );
}

export function EntitiesPanel({ entities }: { entities: DocumentEntities }) {
  const hasAny = entities.numbers.length > 0 || entities.dates.length > 0 || entities.keywords.length > 0;

  return (
    <Card title="Document overview" subtitle="Figures and terms found in the document's text" icon={<FileSearch size={16} />}>
      {hasAny ? (
        <div className="space-y-4">
          <ChipGroup label="Numbers mentioned" values={entities.numbers} />
          <ChipGroup label="Dates mentioned" values={entities.dates} />
          <ChipGroup label="Frequently mentioned terms" values={entities.keywords} />
        </div>
      ) : (
        <EmptyState message="This document is mostly narrative text with no numbers, dates, or repeated terms distinct enough to surface." />
      )}
    </Card>
  );
}
