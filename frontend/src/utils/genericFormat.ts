import type { SemanticType } from '../types/report';
import { formatDate, formatNumber, PLACEHOLDER } from './formatters';

export function formatCellValue(value: unknown, semanticType: SemanticType): string {
  if (value === null || value === undefined || value === '') return PLACEHOLDER;

  switch (semanticType) {
    case 'date':
    case 'datetime':
      return formatDate(String(value));
    case 'currency':
    case 'number':
    case 'quantity': {
      const n = typeof value === 'number' ? value : Number(String(value).replace(/[^0-9.-]/g, ''));
      return Number.isFinite(n) ? formatNumber(n, Number.isInteger(n) ? 0 : 2) : String(value);
    }
    case 'percentage': {
      const n = typeof value === 'number' ? value : Number(String(value).replace(/[^0-9.-]/g, ''));
      return Number.isFinite(n) ? `${formatNumber(n, 2)}%` : String(value);
    }
    case 'boolean':
      return String(value);
    default:
      return String(value);
  }
}

export function isRightAligned(semanticType: SemanticType): boolean {
  return semanticType === 'number' || semanticType === 'currency' || semanticType === 'quantity' || semanticType === 'percentage';
}

export function aggregateForChart(
  rows: Record<string, unknown>[],
  xField: string,
  yField: string,
): { x: string; y: number }[] {
  const totals = new Map<string, number>();
  for (const row of rows) {
    const xValue = row[xField];
    const yValue = row[yField];
    if (xValue === null || xValue === undefined || xValue === '') continue;
    const numeric = typeof yValue === 'number' ? yValue : Number(String(yValue ?? '').replace(/[^0-9.-]/g, ''));
    if (!Number.isFinite(numeric)) continue;
    const key = String(xValue);
    totals.set(key, (totals.get(key) ?? 0) + numeric);
  }
  const points = Array.from(totals.entries()).map(([x, y]) => ({ x, y }));

  const allParseAsDates = points.length > 0 && points.every((p) => !Number.isNaN(Date.parse(p.x)));
  if (allParseAsDates) {
    points.sort((a, b) => Date.parse(a.x) - Date.parse(b.x));
  }
  return points;
}
