import { Capabilities } from '../components/landing/Capabilities';
import { DashboardPreview } from '../components/landing/DashboardPreview';
import { DataQuality } from '../components/landing/DataQuality';
import { ExportWorkflow } from '../components/landing/ExportWorkflow';
import { FinalCta } from '../components/landing/FinalCta';
import { Hero } from '../components/landing/Hero';
import { HowItWorks } from '../components/landing/HowItWorks';
import { LandingFooter } from '../components/landing/LandingFooter';
import { LandingNav } from '../components/landing/LandingNav';
import { Security } from '../components/landing/Security';
import { SupportedFormats } from '../components/landing/SupportedFormats';
import { UseCases } from '../components/landing/UseCases';

export function LandingPage() {
  return (
    <div style={{ background: 'var(--bg)' }}>
      <LandingNav />
      <Hero />
      <SupportedFormats />
      <HowItWorks />
      <Capabilities />
      <UseCases />
      <DataQuality />
      <DashboardPreview />
      <ExportWorkflow />
      <Security />
      <FinalCta />
      <LandingFooter />
    </div>
  );
}
