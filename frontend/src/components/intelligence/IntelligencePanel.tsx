import { Search } from 'lucide-react';
import { useCallback, useState } from 'react';

import { Spinner } from '../common/Spinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { getAnalysis } from '../../api/analysis';
import { getApiErrorMessage } from '../../api/client';
import type { AnalysisBundle } from '../../types/intelligence';
import type { Dataset, DocumentChart, DocumentMetric } from '../../types/report';

import { InvestigatePanel } from './InvestigatePanel';
import { AnomalyRadar } from './AnomalyRadar';
import { DataForensics } from './DataForensics';
import { WhatMattersMost } from './WhatMattersMost';
import { RelationshipGraph } from './RelationshipGraph';
import { GeographicIntelligence } from './GeographicIntelligence';
import { DocumentVision } from './DocumentVision';
import { TradingView } from './TradingView';
import { IntelligentAlerts } from './IntelligentAlerts';
import { TimeMachine } from './TimeMachine';
import { WhatIfSimulator } from './WhatIfSimulator';
import { AIDashboardBuilder } from './AIDashboardBuilder';
import { ExplainPanel } from './ExplainPanel';

interface IntelligencePanelProps {
  reportId: string;
  metrics?: DocumentMetric[];
  charts?: DocumentChart[];
  datasets?: Dataset[];
}

export function IntelligencePanel({ reportId, metrics = [], charts = [], datasets }: IntelligencePanelProps) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'loaded' | 'error'>('idle');
  const [analysis, setAnalysis] = useState<AnalysisBundle | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runInvestigation = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const data = await getAnalysis(reportId);
      setAnalysis(data);
      setStatus('loaded');
    } catch (err) {
      setError(getApiErrorMessage(err));
      setStatus('error');
    }
  }, [reportId]);

  if (status === 'idle') {
    return (
      <div
        className="flex flex-col items-center gap-3 rounded-lg border border-dashed px-6 py-10 text-center"
        style={{ borderColor: 'var(--border-strong)' }}
      >
        <Search size={26} strokeWidth={1.5} style={{ color: 'var(--text-muted)' }} />
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Advanced Intelligence</p>
          <p className="mt-1 max-w-md text-xs" style={{ color: 'var(--text-secondary)' }}>
            One click runs Anomaly Radar, Data Forensics, Discoveries, Relationships, Geography, Vision, and more all computed deterministically from this document's own data.
          </p>
        </div>
        <button
          type="button"
          onClick={runInvestigation}
          className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition hover:opacity-90"
          style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
        >
          <Search size={15} />
          Investigate Document
        </button>
      </div>
    );
  }

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center gap-2 rounded-lg border px-6 py-10" style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
        <Spinner size={18} />
        <span className="text-sm">Investigating…</span>
      </div>
    );
  }

  if (status === 'error') {
    return <ErrorMessage title="Investigation failed" message={error ?? 'Something went wrong.'} onRetry={runInvestigation} />;
  }

  if (!analysis) return null;

  return (
    <div className="space-y-6">
      <InvestigatePanel investigate={analysis.investigate} />
      <div className="grid gap-6 lg:grid-cols-2">
        <AnomalyRadar anomalies={analysis.anomalies} />
        <DataForensics forensics={analysis.forensics} />
      </div>
      <WhatMattersMost findings={analysis.what_matters_most} />
      {analysis.trading && <TradingView trading={analysis.trading} />}
      {(metrics.length > 0 || charts.length > 0) && <ExplainPanel reportId={reportId} metrics={metrics} charts={charts} />}
      {metrics.length > 0 && <WhatIfSimulator metrics={metrics} />}
      <AIDashboardBuilder reportId={reportId} datasets={datasets} />
      <div className="grid gap-6 lg:grid-cols-2">
        <RelationshipGraph graph={analysis.relationships} />
        <GeographicIntelligence geography={analysis.geography} />
      </div>
      <DocumentVision vision={analysis.vision} />
      <IntelligentAlerts reportId={reportId} alerts={analysis.alerts} onChange={runInvestigation} />
      <TimeMachine reportId={reportId} />
    </div>
  );
}
