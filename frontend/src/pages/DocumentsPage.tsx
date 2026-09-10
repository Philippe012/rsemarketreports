import { UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';

import { bulkDeleteReports, deleteReport, listReports, renameReport } from '../api/reports';
import { getApiErrorMessage } from '../api/client';
import { BulkActionsBar } from '../components/documents/BulkActionsBar';
import { DocumentFilterBar } from '../components/documents/DocumentFilterBar';
import { DocumentRowSkeleton, DocumentsTable } from '../components/documents/DocumentsTable';
import { Pagination } from '../components/documents/Pagination';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { useDocumentsList } from '../hooks/useDocumentsList';

export function DocumentsPage() {
  const { params, patchParams, data, error, loading, selected, setSelected, toggleSelect, toggleSelectAll, reload } =
    useDocumentsList(listReports);

  const handleRename = async (id: string, name: string) => {
    await renameReport(id, name);
    reload();
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this document? This cannot be undone.')) return;
    try {
      await deleteReport(id);
      reload();
    } catch (err) {
      window.alert(getApiErrorMessage(err));
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${selected.size} document(s)? This cannot be undone.`)) return;
    try {
      await bulkDeleteReports([...selected]);
      setSelected(new Set());
      reload();
    } catch (err) {
      window.alert(getApiErrorMessage(err));
    }
  };

  return (
    <div className="mx-auto max-w-[1400px] space-y-5 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Documents</h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>Every document you&rsquo;ve uploaded, in one place.</p>
        </div>
        <Link
          to="/app"
          className="inline-flex shrink-0 items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition hover:opacity-90"
          style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}
        >
          <UploadCloud size={15} />
          <span>New document</span>
        </Link>
      </div>

      <DocumentFilterBar params={params} onChange={patchParams} facets={data?.facets ?? null} />

      <BulkActionsBar count={selected.size} onDelete={() => void handleBulkDelete()} onClear={() => setSelected(new Set())} />

      {error && <ErrorMessage message={error} onRetry={reload} />}

      {!error && loading && (
        <div className="divide-y rounded-lg border animate-fade-in" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} style={{ borderColor: 'var(--border)' }}>
              <DocumentRowSkeleton />
            </div>
          ))}
        </div>
      )}

      {!error && !loading && data && data.results.length === 0 && (
        <EmptyState
          icon={<UploadCloud size={26} strokeWidth={1.5} />}
          message={params.search ? `No documents match "${params.search}".` : 'No documents yet. Upload your first PDF, Excel, Word, CSV or TXT file to get started.'}
        />
      )}

      {!error && !loading && data && data.results.length > 0 && (
        <div className="space-y-3 animate-fade-in">
          <DocumentsTable
            reports={data.results}
            selected={selected}
            onToggleSelect={toggleSelect}
            onToggleSelectAll={toggleSelectAll}
            onRename={handleRename}
            onDelete={(id) => void handleDelete(id)}
          />
          <Pagination page={data.page} totalPages={data.total_pages} count={data.count} onChange={(page) => patchParams({ page })} />
        </div>
      )}
    </div>
  );
}
