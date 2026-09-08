import { BarChart3, FileCheck2, ShieldCheck } from 'lucide-react';

import logoIcon from '../assets/logo-icon-square.png';
import { UploadZone } from '../components/upload/UploadZone';
import type { UploadStatus } from '../hooks/useReportUpload';

interface HomeProps {
  status: UploadStatus;
  progress: number;
  fileName: string | null;
  errorMessage: string | null;
  onFileSelected: (file: File) => void;
  onRetry: () => void;
}

const FEATURES = [
  {
    icon: FileCheck2,
    title: 'PDF & Excel support',
    description: 'Upload the RSE market report as-is PDF or Excel no reformatting needed.',
  },
  {
    icon: ShieldCheck,
    title: 'Deterministic extraction',
    description: 'Numbers are parsed and validated with rules, never guessed nothing is invented.',
  },
  {
    icon: BarChart3,
    title: 'Review before export',
    description: 'See the full structured dashboard first, then download an organized Excel workbook.',
  },
];

export function Home({ status, progress, fileName, errorMessage, onFileSelected, onRetry }: HomeProps) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-10 px-4 py-16 sm:px-6">
      <div className="text-center">
        <img src={logoIcon} alt="RSE Report Dashboard" className="mx-auto mb-5 h-16 w-16 object-contain" />
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl" style={{ color: 'var(--text)' }}>
          Turn an RSE report into a dashboard
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-[15px]" style={{ color: 'var(--text-secondary)' }}>
          Upload a Rwanda Stock Exchange market report and get a clean, structured, reviewable dashboard
          then export it back to a well-organized Excel workbook.
        </p>
      </div>

      <UploadZone
        status={status}
        progress={progress}
        fileName={fileName}
        errorMessage={errorMessage}
        onFileSelected={onFileSelected}
        onRetry={onRetry}
      />

      <div className="grid w-full grid-cols-1 gap-4 sm:grid-cols-3">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border p-4 text-left"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
          >
            <div
              className="mb-3 flex h-9 w-9 items-center justify-center rounded-md"
              style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}
            >
              <feature.icon size={17} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{feature.title}</p>
            <p className="mt-1 text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              {feature.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
