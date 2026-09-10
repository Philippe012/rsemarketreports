import { ArrowDown, ArrowUp } from 'lucide-react';
import { useMemo, useState } from 'react';

import { TD, TH, TableShell } from '../dashboard/TableShell';
import type { Dataset } from '../../types/report';
import { formatCellValue, isRightAligned } from '../../utils/genericFormat';
import { EmptyState } from '../common/EmptyState';
import { SearchInput } from '../common/SearchInput';

const PAGE_SIZE = 25;

export function DatasetTable({ dataset }: { dataset: Dataset }) {
  const [query, setQuery] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);

  const columns = dataset.columns;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return dataset.rows;
    return dataset.rows.filter((row) =>
      columns.some((col) => String(row[col.name] ?? '').toLowerCase().includes(q)),
    );
  }, [dataset.rows, columns, query]);

  const sorted = useMemo(() => {
    if (!sortColumn) return filtered;
    const copy = [...filtered];
    copy.sort((a, b) => {
      const av = a[sortColumn];
      const bv = b[sortColumn];
      const an = typeof av === 'number' ? av : Number(av);
      const bn = typeof bv === 'number' ? bv : Number(bv);
      let cmp: number;
      if (Number.isFinite(an) && Number.isFinite(bn)) {
        cmp = an - bn;
      } else {
        cmp = String(av ?? '').localeCompare(String(bv ?? ''));
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return copy;
  }, [filtered, sortColumn, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages - 1);
  const pageRows = sorted.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE);

  const toggleSort = (columnName: string) => {
    if (sortColumn === columnName) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortColumn(columnName);
      setSortDir('asc');
    }
    setPage(0);
  };

  if (dataset.rows.length === 0) {
    return <EmptyState message="This dataset has no rows." />;
  }

  return (
    <div className="space-y-3">
      {dataset.rows.length > 8 && (
        <div className="flex justify-end">
          <SearchInput value={query} onChange={(v) => { setQuery(v); setPage(0); }} placeholder="Search this table…" />
        </div>
      )}
      <TableShell>
        <thead>
          <tr>
            {columns.map((col) => (
              <TH key={col.name} align={isRightAligned(col.semantic_type) ? 'right' : 'left'}>
                <button
                  type="button"
                  onClick={() => toggleSort(col.name)}
                  className="inline-flex items-center gap-1 uppercase tracking-wide"
                >
                  {col.display_name}
                  {sortColumn === col.name && (sortDir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />)}
                </button>
              </TH>
            ))}
          </tr>
        </thead>
        <tbody>
          {pageRows.map((row, i) => (
            <tr key={i} className="table-row-hover">
              {columns.map((col) => (
                <TD key={col.name} align={isRightAligned(col.semantic_type) ? 'right' : 'left'}>
                  {formatCellValue(row[col.name], col.semantic_type)}
                </TD>
              ))}
            </tr>
          ))}
          {pageRows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                No rows match “{query}”.
              </td>
            </tr>
          )}
        </tbody>
      </TableShell>
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs" style={{ color: 'var(--text-secondary)' }}>
          <span>
            {sorted.length} row{sorted.length === 1 ? '' : 's'} · page {currentPage + 1} of {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={currentPage === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="rounded-md border px-2.5 py-1 disabled:opacity-40"
              style={{ borderColor: 'var(--border)' }}
            >
              Previous
            </button>
            <button
              type="button"
              disabled={currentPage >= totalPages - 1}
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              className="rounded-md border px-2.5 py-1 disabled:opacity-40"
              style={{ borderColor: 'var(--border)' }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
