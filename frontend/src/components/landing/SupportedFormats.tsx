import { FileSpreadsheet, FileText, FileType, Table } from 'lucide-react';

const FORMATS = [
  { icon: FileText, label: 'PDF', description: 'Reports, statements, scanned tables' },
  { icon: FileSpreadsheet, label: 'Excel', description: '.xlsx, .xls, .xlsm, multi-sheet' },
  { icon: FileType, label: 'Word', description: '.docx narrative + embedded tables' },
  { icon: Table, label: 'CSV', description: 'Delimited exports from any system' },
  { icon: FileText, label: 'TXT', description: 'Plain text, notes, logs' },
];

export function SupportedFormats() {
  return (
    <div className="border-y" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
      <div className="mx-auto max-w-[1400px] px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-6">
          {FORMATS.map((format) => (
            <div key={format.label} className="flex items-center gap-3">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-md"
                style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}
              >
                <format.icon size={16} />
              </div>
              <div>
                <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{format.label}</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{format.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
