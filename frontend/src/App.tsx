import { Header } from './components/layout/Header';
import { ThemeProvider } from './context/ThemeContext';
import { useReportUpload } from './hooks/useReportUpload';
import { Dashboard } from './pages/Dashboard';
import { Home } from './pages/Home';

function AppContent() {
  const { status, progress, report, errorMessage, fileName, upload, reset } = useReportUpload();
  const showDashboard = status === 'success' && report?.status === 'completed';

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      <Header showNewUpload={showDashboard} onNewUpload={reset} />
      <main>
        {showDashboard && report ? (
          <Dashboard report={report} onBackToReports={reset} />
        ) : (
          <Home
            status={status}
            progress={progress}
            fileName={fileName}
            errorMessage={errorMessage}
            onFileSelected={upload}
            onRetry={reset}
          />
        )}
      </main>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
