import { Share2 } from 'lucide-react';
import { useMemo } from 'react';

import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import type { RelationshipGraph as RelationshipGraphData } from '../../types/intelligence';

const SIZE = 360;
const CENTER = SIZE / 2;
const RADIUS = SIZE / 2 - 48;

export function RelationshipGraph({ graph }: { graph: RelationshipGraphData }) {
  const positions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>();
    graph.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / Math.max(graph.nodes.length, 1) - Math.PI / 2;
      map.set(node.id, { x: CENTER + RADIUS * Math.cos(angle), y: CENTER + RADIUS * Math.sin(angle) });
    });
    return map;
  }, [graph.nodes]);

  const edgeColor = 'var(--border-strong)';
  const nodeFill = 'var(--surface-hover)';

  return (
    <Card title="Entity Relationship Graph" subtitle="Values that co-occur in the same row, and correlated numeric columns" icon={<Share2 size={16} />}>
      {graph.nodes.length === 0 ? (
        <EmptyState message="No relationships between entities were detected in this document." />
      ) : (
        <div className="flex flex-col items-center gap-4 lg:flex-row lg:items-start">
          <svg width={SIZE} height={SIZE} className="shrink-0">
            {graph.edges.map((edge, i) => {
              const a = positions.get(edge.source);
              const b = positions.get(edge.target);
              if (!a || !b) return null;
              return (
                <line
                  key={i}
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke={edgeColor}
                  strokeWidth={Math.min(1 + edge.weight / 3, 6)}
                />
              );
            })}
            {graph.nodes.map((node) => {
              const p = positions.get(node.id);
              if (!p) return null;
              return (
                <g key={node.id}>
                  <circle cx={p.x} cy={p.y} r={node.type === 'measure' ? 8 : 6} fill={nodeFill} stroke="var(--brand)" strokeWidth={1.5} />
                  <text x={p.x} y={p.y - 12} textAnchor="middle" fontSize={10} fill="var(--text-secondary)">
                    {node.label.length > 14 ? `${node.label.slice(0, 13)}…` : node.label}
                  </text>
                </g>
              );
            })}
          </svg>
          <ul className="w-full min-w-0 space-y-2 text-sm">
            {graph.edges.slice(0, 12).map((edge, i) => {
              const sourceLabel = graph.nodes.find((n) => n.id === edge.source)?.label ?? edge.source;
              const targetLabel = graph.nodes.find((n) => n.id === edge.target)?.label ?? edge.target;
              return (
                <li key={i} className="rounded-md border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
                  <span style={{ color: 'var(--text)' }}>{sourceLabel} ↔ {targetLabel}</span>
                  <span className="ml-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                    {edge.type === 'correlates'
                      ? `correlation ${edge.correlation} across ${edge.evidence_count} row(s)`
                      : `co-occurs in ${edge.weight} row(s)`}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </Card>
  );
}
