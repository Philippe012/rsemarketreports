import { Download } from 'lucide-react';
import { useState } from 'react';

import { getDownloadUrl } from '../../api/reports';
import { Spinner } from '../common/Spinner';

export function ExportButton({ reportId, variant = 'solid' }: { reportId: string; variant?: 'solid' | 'outline' }) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      const response = await fetch(getDownloadUrl(reportId));
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const disposition = response.headers.get('Content-Disposition') ?? '';
      const match = /filename="?([^";]+)"?/.exec(disposition);
      const filename = match?.[1] ?? `RSE_Report_${reportId}.xlsx`;

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      window.open(getDownloadUrl(reportId), '_blank');
    } finally {
      setIsDownloading(false);
    }
  };

  const isSolid = variant === 'solid';

  return (
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
  );
}
