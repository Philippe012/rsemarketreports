import type { Severity } from '../../types/intelligence';

export function severityTone(severity: Severity): 'negative' | 'warning' | 'neutral' {
  if (severity === 'high') return 'negative';
  if (severity === 'medium') return 'warning';
  return 'neutral';
}
