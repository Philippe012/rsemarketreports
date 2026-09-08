import { useCallback, useRef, useState } from 'react';

import { uploadReport } from '../api/reports';
import { getApiErrorMessage } from '../api/client';
import type { Report } from '../types/report';

export type UploadStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

interface UploadState {
  status: UploadStatus;
  progress: number;
  report: Report | null;
  errorMessage: string | null;
  fileName: string | null;
}

const initialState: UploadState = {
  status: 'idle',
  progress: 0,
  report: null,
  errorMessage: null,
  fileName: null,
};

export function useReportUpload() {
  const [state, setState] = useState<UploadState>(initialState);
  const requestId = useRef(0);

  const upload = useCallback(async (file: File) => {
    const id = ++requestId.current;
    setState({ status: 'uploading', progress: 0, report: null, errorMessage: null, fileName: file.name });

    try {
      const report = await uploadReport(file, (percent) => {
        if (requestId.current !== id) return;
        setState((prev) => ({
          ...prev,
          progress: percent,
          status: percent >= 100 ? 'processing' : 'uploading',
        }));
      });
      if (requestId.current !== id) return;

      if (report.status === 'failed') {
        setState((prev) => ({
          ...prev,
          status: 'error',
          errorMessage: report.error_message || 'The document could not be processed.',
        }));
        return;
      }

      setState((prev) => ({ ...prev, status: 'success', report, progress: 100 }));
    } catch (error) {
      if (requestId.current !== id) return;
      setState((prev) => ({ ...prev, status: 'error', errorMessage: getApiErrorMessage(error) }));
    }
  }, []);

  const reset = useCallback(() => {
    requestId.current += 1;
    setState(initialState);
  }, []);

  return { ...state, upload, reset };
}
