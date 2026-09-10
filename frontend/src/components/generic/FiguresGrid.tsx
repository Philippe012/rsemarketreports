import { ImageIcon } from 'lucide-react';

import type { DocumentFigure } from '../../types/report';
import { Card } from '../common/Card';

/** Embedded images found in the document. Shown as-is with their source
 * location — the platform never tries to read chart values out of an image,
 * so no data claims are attached to a figure, only what it literally is. */
export function FiguresGrid({ figures }: { figures: DocumentFigure[] }) {
  if (figures.length === 0) return null;

  return (
    <Card
      title="Figures"
      subtitle={`${figures.length} image${figures.length === 1 ? '' : 's'} found in the document`}
      icon={<ImageIcon size={16} />}
    >
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {figures.map((figure, i) => (
          <div key={i} className="overflow-hidden rounded-lg border" style={{ borderColor: 'var(--border)' }}>
            <div className="flex aspect-[4/3] items-center justify-center" style={{ background: 'var(--bg-subtle)' }}>
              {figure.thumbnail ? (
                <img src={figure.thumbnail} alt={`Figure from ${figure.source}`} className="h-full w-full object-contain" />
              ) : (
                <ImageIcon size={24} style={{ color: 'var(--text-muted)' }} />
              )}
            </div>
            <div className="px-2.5 py-2">
              <p className="text-xs font-medium" style={{ color: 'var(--text)' }}>{figure.source}</p>
              {figure.width && figure.height && (
                <p className="text-[11px] tabular-nums" style={{ color: 'var(--text-muted)' }}>
                  {figure.width} × {figure.height}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
