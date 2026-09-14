import { ShieldCheck } from 'lucide-react';

import { bulkDeleteReports, listAllReportsAdmin, renameReport } from '../api/reports';
import { getApiErrorMessage } from '../api/client';
import { BulkActionsBar } from '../components/documents/BulkActionsBar';
import { DocumentFilterBar } from '../components/documents/DocumentFilterBar';
import { DocumentRowSkeleton, DocumentsTable } from '../components/documents/DocumentsTable';
import { Pagination } from '../components/documents/Pagination';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { useDocumentsList } from '../hooks/useDocumentsList';

export function AdminDocumentsPage() {
  const { params, patchParams, data, error, loading, selected, setSelected, toggleSelect, toggleSelectAll, reload } =
    useDocumentsList(listAllReportsAdmin);

  const handleRename = async (id: string, name: string) => {
    await renameReport(id, name);
    reload();
  };

  const handleDelete = async (id: string) => {
    try {
      await bulkDeleteReports([id]);
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
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}>
          <ShieldCheck size={16} />
        </div>
        <div>
          <h1 className="text-xl font-semibold tracking-tight" style={{ color: 'var(--text)' }}>Admin · All documents</h1>
          <p className="mt-0.5 text-sm" style={{ color: 'var(--text-secondary)' }}>Every document uploaded by every user.</p>
        </div>
      </div>

      <DocumentFilterBar params={params} onChange={patchParams} facets={data?.facets ?? null} showOwnerFilter />

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
        <EmptyState message="No documents match these filters." />
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
            showOwner
          />
          <Pagination page={data.page} totalPages={data.total_pages} count={data.count} onChange={(page) => patchParams({ page })} />
        </div>
      )}
    </div>
  );
}
