import { Globe2 } from 'lucide-react';
import { ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts';

import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { formatNumber } from '../../utils/formatters';
import type { GeographicIntelligence as GeoData } from '../../types/intelligence';

export function GeographicIntelligence({ geography }: { geography: GeoData }) {
  return (
    <Card title="Geographic Intelligence" subtitle="Locations detected in the data, plotted by coordinate" icon={<Globe2 size={16} />}>
      {!geography.has_geo ? (
        <EmptyState message="No location data (coordinates or recognized place names) was found in this document." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                <XAxis type="number" dataKey="lon" name="Longitude" tick={{ fontSize: 11 }} domain={['dataMin - 5', 'dataMax + 5']} />
                <YAxis type="number" dataKey="lat" name="Latitude" tick={{ fontSize: 11 }} domain={['dataMin - 5', 'dataMax + 5']} />
                <ZAxis type="number" dataKey="value" range={[60, 300]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const point = payload[0].payload as GeoData['points'][number];
                    return (
                      <div className="rounded-md border px-3 py-2 text-sm shadow-lg" style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}>
                        <p className="font-medium">{point.label}</p>
                        {point.value !== null && <p className="tabular-nums">{formatNumber(point.value, 2)}</p>}
                      </div>
                    );
                  }}
                />
                <Scatter data={geography.points} fill="var(--brand)" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <ul className="space-y-2 text-sm">
            {geography.points.slice(0, 10).map((point, i) => (
              <li key={i} className="flex items-center justify-between rounded-md border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                <span style={{ color: 'var(--text)' }}>{point.label}</span>
                <span className="tabular-nums text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {point.value !== null ? formatNumber(point.value, 2) : '—'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
