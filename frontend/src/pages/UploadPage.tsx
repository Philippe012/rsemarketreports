import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { UploadZone } from '../components/upload/UploadZone';
import { useReportUpload } from '../hooks/useReportUpload';

export function UploadPage() {
  const { status, progress, report, errorMessage, fileName, upload, reset } = useReportUpload();
  const navigate = useNavigate();

  useEffect(() => {
    if (status === 'success' && report) {
      navigate(`/app/documents/${report.id}`);
    }
  }, [status, report, navigate]);

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-8 px-4 py-16 sm:px-6">
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl" style={{ color: 'var(--text)' }}>
          Upload a document
        </h1>
        <p className="mx-auto mt-2.5 max-w-lg text-sm" style={{ color: 'var(--text-secondary)' }}>
          Your document is structured into datasets, metrics and charts automatically. Recognized
          formats like RSE market reports get their own specialized dashboard.
        </p>
      </div>

      <UploadZone
        status={status}
        progress={progress}
        fileName={fileName}
        errorMessage={errorMessage}
        onFileSelected={upload}
        onRetry={reset}
      />
    </div>
  );
}
