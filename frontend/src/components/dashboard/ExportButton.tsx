import { Braces, Download } from 'lucide-react';
import { useState } from 'react';

import { getDownloadUrl, getJsonDownloadUrl } from '../../api/reports';
import { Spinner } from '../common/Spinner';

async function downloadFile(url: string, fallbackFilename: string) {
  const response = await fetch(url, { credentials: 'include' });
  if (!response.ok) throw new Error('Download failed');
  const blob = await response.blob();
  const disposition = response.headers.get('Content-Disposition') ?? '';
  const match = /filename="?([^";]+)"?/.exec(disposition);
  const filename = match?.[1] ?? fallbackFilename;

  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
}

export function ExportButton({ reportId, variant = 'solid' }: { reportId: string; variant?: 'solid' | 'outline' }) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [isDownloadingJson, setIsDownloadingJson] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await downloadFile(getDownloadUrl(reportId), `RSE_Report_${reportId}.xlsx`);
    } catch {
      window.open(getDownloadUrl(reportId), '_blank');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadJson = async () => {
    setIsDownloadingJson(true);
    try {
      await downloadFile(getJsonDownloadUrl(reportId), `report_${reportId}.json`);
    } catch {
      window.open(getJsonDownloadUrl(reportId), '_blank');
    } finally {
      setIsDownloadingJson(false);
    }
  };

  const isSolid = variant === 'solid';

  return (
    <div className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={handleDownload}
        disabled={isDownloading}
        className="inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition hover:opacity-90 disabled:opacity-60"
        style={
          isSolid
            ? { background: 'var(--brand)', color: 'var(--brand-contrast)' }
            : { border: '1px solid var(--border-strong)', color: 'var(--text)', background: 'var(--surface)' }
        }
      >
        {isDownloading ? <Spinner size={15} /> : <Download size={15} />}
        Download Excel workbook
      </button>
      <button
        type="button"
        onClick={handleDownloadJson}
        disabled={isDownloadingJson}
        title="Download the same validated data as JSON"
        aria-label="Download JSON"
        className="inline-flex items-center justify-center rounded-lg p-2.5 transition hover:opacity-90 disabled:opacity-60"
        style={{ border: '1px solid var(--border-strong)', color: 'var(--text)', background: 'var(--surface)' }}
      >
        {isDownloadingJson ? <Spinner size={15} /> : <Braces size={15} />}
      </button>
    </div>
  );
}
