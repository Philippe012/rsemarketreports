import { CheckCircle2, ChevronRight, Download, FileSearch, LayoutDashboard, UploadCloud } from 'lucide-react';
import { Section } from './Section';

const STEPS = [
  { icon: UploadCloud, title: 'Upload', description: 'Drop in a PDF, Excel, Word, CSV or TXT file no template or setup required.' },
  { icon: FileSearch, title: 'Extract', description: 'Text and tables are parsed deterministically: rows, columns, figures and structure are all recovered.' },
  { icon: CheckCircle2, title: 'Validate', description: 'Numbers are checked against the source and duplicates are flagged every issue surfaces as a warning, never silently.' },
  { icon: LayoutDashboard, title: 'Visualize', description: 'KPIs, charts and tables are generated automatically, tailored to what the document contains.' },
  { icon: Download, title: 'Export', description: 'Download an organized, formatted Excel workbook whenever you need the data outside the dashboard.' },
];

export function HowItWorks() {
  return (
    <Section
      id="how-it-works"
      eyebrow="How it works"
      heading="From document to dashboard in five steps"
      subheading="The same deterministic pipeline runs on every upload nothing is invented, and every number traces back to the source."
    >
      <div className="steps-row">
        {STEPS.map((step, i) => (
          <div key={step.title} className="step-item">
            <div className="step-connector" aria-hidden="true" />
            <div className="step-chevron" aria-hidden="true">
              <ChevronRight size={13} />
            </div>

            <div className="step-circle">
              <step.icon size={26} strokeWidth={1.75} />
            </div>

            <div className="step-text">
              <p className="step-eyebrow">{`Step ${String(i + 1).padStart(2, '0')}`}</p>
              <p className="step-title">{step.title}</p>
              <p className="step-description">{step.description}</p>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}