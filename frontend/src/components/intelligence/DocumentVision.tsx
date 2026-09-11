import { Eye } from 'lucide-react';

import { Card } from '../common/Card';
import type { VisionSummary } from '../../types/intelligence';

export function DocumentVision({ vision }: { vision: VisionSummary }) {
  const tiles = [
    { label: 'Tables', value: vision.tables_detected },
    { label: 'Suggested charts', value: vision.charts_suggested },
    { label: 'Chart-like figures', value: vision.figures_chart_like },
    { label: 'Photos / diagrams', value: vision.figures_photo_or_diagram },
    { label: 'Forms', value: vision.forms_detected },
  ];
  return (
    <Card title="Document Vision" subtitle="Structural inventory of tables, charts, and figures found" icon={<Eye size={16} />}>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {tiles.map((tile) => (
          <div key={tile.label} className="rounded-md border px-3 py-3 text-center" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xl font-semibold tabular-nums" style={{ color: 'var(--text)' }}>{tile.value}</p>
            <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>{tile.label}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
