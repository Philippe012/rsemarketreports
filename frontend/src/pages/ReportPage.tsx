import { useEffect, useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';

import { getReport } from '../api/reports';
import { getApiErrorMessage } from '../api/client';
import { DocumentChat } from '../components/chat/DocumentChat';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Spinner } from '../components/common/Spinner';
import type { Report } from '../types/report';
import { Dashboard } from './Dashboard';

export function ReportPage() {
  const { id } = useParams<{ id: string }>();
  if (!id) return <Navigate to="/app/documents" replace />;
  return <ReportPageContent key={id} id={id} />;
}

function ReportPageContent({ id }: { id: string }) {
  const navigate = useNavigate();
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getReport(id)
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err) => {
        if (!cancelled) setError(getApiErrorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-[1400px] px-4 py-16 sm:px-6 lg:px-8">
        <ErrorMessage title="Couldn't load this document" message={error} onRetry={() => navigate('/app/documents')} />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Spinner size={28} />
      </div>
    );
  }

  if (report.status !== 'completed' || !report.extracted_data) {
    return (
      <div className="mx-auto max-w-[1400px] px-4 py-16 sm:px-6 lg:px-8">
        <ErrorMessage
          title={report.status === 'failed' ? 'Processing failed' : 'Still processing'}
          message={report.error_message || 'This document has not finished processing yet.'}
          onRetry={() => navigate('/app/documents')}
        />
      </div>
    );
  }

  const title = report.extracted_data.kind === 'rse_market_report'
    ? report.extracted_data.report_title || 'Rwanda Stock Exchange Market Report'
    : report.extracted_data.filename;

  return (
    <>
      <Dashboard report={report} />
      <DocumentChat reportId={report.id} documentTitle={title} />
    </>
  );
}
