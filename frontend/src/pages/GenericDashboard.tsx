import { Table2 } from 'lucide-react';
import { useRef } from 'react';

import { Card } from '../components/common/Card';
import { InsightsList } from '../components/common/InsightsList';
import { DocumentHeader } from '../components/dashboard/DocumentHeader';
import { ExportButton } from '../components/dashboard/ExportButton';
import { DatasetChart } from '../components/generic/DatasetChart';
import { DatasetTable } from '../components/generic/DatasetTable';
import { EntitiesPanel } from '../components/generic/EntitiesPanel';
import { FiguresGrid } from '../components/generic/FiguresGrid';
import { MetricsGrid } from '../components/generic/MetricsGrid';
import { SectionsList } from '../components/generic/SectionsList';
import type { GenericReport } from '../types/report';

const LOW_CONFIDENCE_NOTE: Record<string, string | null> = {
  high: null,
  medium: 'Best-guess classification — review before relying on it.',
  low: 'Could not confidently classify this document.',
};

export function GenericDashboard({ report }: { report: GenericReport }) {
  const document = report.extracted_data;
  const hasDatasets = document.datasets.length > 0;
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const datasetCount = document.datasets.length;
  const totalRecords = document.datasets.reduce((sum, d) => sum + d.row_count, 0);
  const summary = hasDatasets
    ? `${datasetCount} dataset${datasetCount === 1 ? '' : 's'} · ${totalRecords.toLocaleString()} record${totalRecords === 1 ? '' : 's'}`
    : `${document.sections.length} section${document.sections.length === 1 ? '' : 's'} of text · no tables found`;
  const confidenceNote = LOW_CONFIDENCE_NOTE[document.document_type_confidence];

  const scrollTo = (name: string) => {
    sectionRefs.current[name]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const navItems = [
    { id: 'overview', label: 'Overview', show: true },
    { id: 'insights', label: 'Insights', show: document.insights.length > 0 },
    { id: 'datasets', label: 'Datasets', show: hasDatasets },
    { id: 'figures', label: 'Figures', show: document.figures.length > 0 },
    { id: 'source', label: 'Source', show: document.sections.length > 0 },
  ].filter((item) => item.show);

  return (
    <div className="mx-auto max-w-[1400px] space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <DocumentHeader
        eyebrow={document.document_type}
        title={document.filename}
        sourceType={document.source_type}
        secondaryLine={confidenceNote ? `${summary} · ${confidenceNote}` : summary}
        reportId={report.id}
        warnings={report.warnings}
      />

      {navItems.length > 1 && (
        <nav className="flex flex-wrap gap-2" aria-label="Jump to section">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => scrollTo(item.id)}
              className="rounded-full border px-3 py-1.5 text-xs font-medium transition hover:opacity-80"
              style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text-secondary)' }}
            >
              {item.label}
            </button>
          ))}
        </nav>
      )}

      <div ref={(el) => { sectionRefs.current.overview = el; }}>
        {hasDatasets ? (
          <section>
            <div className="mb-3">
              <h2 className="text-[15px] font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Overview</h2>
              <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>Key figures computed from the extracted data</p>
            </div>
            <MetricsGrid metrics={document.metrics} />
          </section>
        ) : (
          <EntitiesPanel entities={document.entities} />
        )}
      </div>

      {document.insights.length > 0 && (
        <div ref={(el) => { sectionRefs.current.insights = el; }}>
          <InsightsList insights={document.insights} />
        </div>
      )}

      {hasDatasets && (
        <div ref={(el) => { sectionRefs.current.datasets = el; }} className="space-y-6">
          {document.datasets.length > 1 && (
            <nav className="flex flex-wrap gap-2" aria-label="Jump to dataset">
              {document.datasets.map((dataset) => (
                <button
                  key={dataset.name}
                  type="button"
                  onClick={() => scrollTo(`dataset-${dataset.name}`)}
                  className="rounded-full border px-3 py-1.5 text-xs font-medium transition hover:opacity-80"
                  style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text-secondary)' }}
                >
                  {dataset.name}
                  <span className="ml-1.5 tabular-nums" style={{ color: 'var(--text-muted)' }}>{dataset.row_count}</span>
                </button>
              ))}
            </nav>
          )}

          {document.datasets.map((dataset) => {
            const chart = document.charts.find((c) => c.dataset === dataset.name);
            return (
              <div key={dataset.name} ref={(el) => { sectionRefs.current[`dataset-${dataset.name}`] = el; }}>
                <Card
                  title={dataset.name}
                  subtitle={`${dataset.row_count} record${dataset.row_count === 1 ? '' : 's'} · ${dataset.source}`}
                  icon={<Table2 size={16} />}
                >
                  <div className="space-y-6">
                    {chart && <DatasetChart chart={chart} dataset={dataset} />}
                    <DatasetTable dataset={dataset} />
                  </div>
                </Card>
              </div>
            );
          })}
        </div>
      )}

      {document.figures.length > 0 && (
        <div ref={(el) => { sectionRefs.current.figures = el; }}>
          <FiguresGrid figures={document.figures} />
        </div>
      )}

      {document.sections.length > 0 && (
        <div ref={(el) => { sectionRefs.current.source = el; }}>
          <SectionsList sections={document.sections} />
        </div>
      )}

      <div
        className="flex flex-col items-center gap-3 rounded-lg border px-6 py-8 text-center animate-fade-in sm:flex-row sm:justify-between sm:text-left"
        style={{ background: 'var(--brand-soft)', borderColor: 'var(--border)' }}
      >
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Reviewed everything? Export the full document.
          </p>
          <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
            Downloads every dataset above as an organized Excel workbook.
          </p>
        </div>
        <ExportButton reportId={report.id} />
      </div>
    </div>
  );
}
