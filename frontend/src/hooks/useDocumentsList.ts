import { useCallback, useEffect, useState } from 'react';

import { getApiErrorMessage } from '../api/client';
import type { ReportListParams, ReportListResponse, ReportSummary } from '../types/report';

const DEFAULT_PARAMS: ReportListParams = { sort: '-created_at', page: 1, page_size: 20 };

export function useDocumentsList<T extends ReportSummary>(
  fetcher: (params: ReportListParams) => Promise<ReportListResponse<T>>,
) {
  const [params, setParams] = useState<ReportListParams>(DEFAULT_PARAMS);
  const [data, setData] = useState<ReportListResponse<T> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [reloadToken, setReloadToken] = useState(0);

  const patchParams = useCallback((patch: Partial<ReportListParams>) => {
    setParams((prev) => ({ ...prev, ...patch }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    const timeout = setTimeout(() => {
      setLoading(true);
      setError(null);
      fetcher(params)
        .then((res) => {
          if (cancelled) return;
          setData(res);
          setSelected(new Set());
        })
        .catch((err) => {
          if (!cancelled) setError(getApiErrorMessage(err));
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, params.search ? 250 : 0);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
    // fetcher is a stable module-level function reference for each page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, reloadToken]);

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  const toggleSelect = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelected((prev) => {
      if (!data) return prev;
      const allSelected = data.results.length > 0 && data.results.every((r) => prev.has(r.id));
      return allSelected ? new Set() : new Set(data.results.map((r) => r.id));
    });
  }, [data]);

  return {
    params, patchParams, data, error, loading,
    selected, setSelected, toggleSelect, toggleSelectAll, reload,
  };
}
