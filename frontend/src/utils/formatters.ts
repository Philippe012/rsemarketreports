
const PLACEHOLDER = '—';

export function formatNumber(value: number | null | undefined, fractionDigits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  return value.toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatCurrency(value: number | null | undefined, currency = 'FRW'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  return `${currency} ${formatNumber(value, 2)}`;
}

export function formatCompactCurrency(value: number | null | undefined, currency = 'FRW'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${currency} ${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${currency} ${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${currency} ${(value / 1_000).toFixed(1)}K`;
  return formatCurrency(value, currency);
}

/** Compact form for large plain counts (volumes, share counts) — "52,000,000" -> "52M". */
export function formatCompactNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(abs % 1_000_000 === 0 ? 0 : 1)}M`;
  if (abs >= 1_000) return `${(value / 1_000).toFixed(abs % 1_000 === 0 ? 0 : 1)}K`;
  return formatNumber(value);
}

export function formatPercent(value: number | null | undefined, fractionDigits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(fractionDigits)}%`;
}

export function formatPlainPercent(value: number | null | undefined, fractionDigits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  return `${value.toFixed(fractionDigits)}%`;
}

export function formatSignedNumber(value: number | null | undefined, fractionDigits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return PLACEHOLDER;
  const sign = value > 0 ? '+' : '';
  return `${sign}${formatNumber(value, fractionDigits)}`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return PLACEHOLDER;
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' });
}

export function formatShortDate(value: string | null | undefined): string {
  if (!value) return PLACEHOLDER;
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatDateWithWeekday(value: string | null | undefined): string {
  if (!value) return PLACEHOLDER;
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
}

export function trendDirection(value: number | null | undefined): 'up' | 'down' | 'flat' {
  if (value === null || value === undefined || Number.isNaN(value) || value === 0) return 'flat';
  return value > 0 ? 'up' : 'down';
}

export { PLACEHOLDER };
