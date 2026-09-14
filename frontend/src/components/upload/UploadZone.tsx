import { FileSpreadsheet, FileText, FileType, Table, UploadCloud } from 'lucide-react';
import { useCallback, useRef, useState } from 'react';

import { ErrorMessage } from '../common/ErrorMessage';
import { Spinner } from '../common/Spinner';
import type { UploadStatus } from '../../hooks/useReportUpload';

const ACCEPTED_EXTENSIONS = ['.pdf', '.xlsx', '.xls', '.xlsm', '.docx', '.csv', '.txt'];

interface UploadZoneProps {
  status: UploadStatus;
  progress: number;
  fileName: string | null;
  errorMessage: string | null;
  onFileSelected: (file: File) => void;
  onRetry: () => void;
}

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext));
}

export function UploadZone({ status, progress, fileName, errorMessage, onFileSelected, onRetry }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      const file = files?.[0];
      if (!file) return;
      if (!isAcceptedFile(file)) {
        setLocalError('Unsupported file type. Please upload a PDF, Excel, Word (.docx), CSV or TXT document.');
        return;
      }
      setLocalError(null);
      onFileSelected(file);
    },
    [onFileSelected],
  );

  if (status === 'error') {
    return (
      <ErrorMessage
        title="Couldn't process this document"
        message={errorMessage ?? 'An unknown error occurred.'}
        onRetry={onRetry}
      />
    );
  }

  const isBusy = status === 'uploading' || status === 'processing';

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!isBusy) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (!isBusy) handleFiles(e.dataTransfer.files);
        }}
        onClick={() => !isBusy && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isBusy) inputRef.current?.click();
        }}
        className="flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed px-8 py-16 text-center transition-colors"
        style={{
          borderColor: isDragging ? 'var(--brand)' : 'var(--border-strong)',
          background: isDragging ? 'var(--brand-soft)' : 'var(--surface)',
          cursor: isBusy ? 'default' : 'pointer',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {isBusy ? (
          <>
            <div
              className="flex h-14 w-14 items-center justify-center rounded-full"
              style={{ background: 'var(--neutral-icon)', color: 'var(--text-secondary)' }}
            >
              <Spinner size={26} />
            </div>
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                {status === 'uploading' ? `Uploading ${fileName}…` : 'Extracting and validating data…'}
              </p>
              <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                {status === 'uploading'
                  ? 'Please keep this tab open.'
                  : 'Parsing tables, normalizing figures, and checking for issues.'}
              </p>
            </div>
            <div className="h-1.5 w-64 max-w-full overflow-hidden rounded-full" style={{ background: 'var(--bg-subtle)' }}>
              <div
                className="h-full rounded-full transition-all duration-300 ease-out"
                style={{
                  width: status === 'uploading' ? `${progress}%` : '100%',
                  background: 'var(--brand)',
                  ...(status === 'processing' ? { animation: 'shimmer 1.6s linear infinite' } : {}),
                }}
              />
            </div>
          </>
        ) : (
          <>
            <div
              className="flex h-14 w-14 items-center justify-center rounded-full"
              style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}
            >
              <UploadCloud size={26} />
            </div>
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>
                Drag & drop your document, or click to browse
              </p>
              <p className="mt-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                Reports, spreadsheets and datasets with market reports to get a specialized dashboard
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-4 pt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
              <span className="inline-flex items-center gap-1.5">
                <FileText size={14} /> PDF
              </span>
              <span className="inline-flex items-center gap-1.5">
                <FileSpreadsheet size={14} /> Excel
              </span>
              <span className="inline-flex items-center gap-1.5">
                <FileType size={14} /> Word
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Table size={14} /> CSV
              </span>
              <span className="inline-flex items-center gap-1.5">
                <FileText size={14} /> TXT
              </span>
            </div>
          </>
        )}
      </div>
      {localError && (
        <p className="mt-3 text-center text-sm" style={{ color: 'var(--negative)' }}>
          {localError}
        </p>
      )}
    </div>
  );
}
