import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/routing/ProtectedRoute';
import { PublicOnlyRoute } from './components/routing/PublicOnlyRoute';
import { StaffRoute } from './components/routing/StaffRoute';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { AdminDocumentsPage } from './pages/AdminDocumentsPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/auth/LoginPage';
import { ReportPage } from './pages/ReportPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { SettingsPage } from './pages/SettingsPage';
import { SignupPage } from './pages/auth/SignupPage';
import { UploadPage } from './pages/UploadPage';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />

          <Route element={<PublicOnlyRoute />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password/:uid/:token" element={<ResetPasswordPage />} />
          </Route>

          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<AppShell />}>
              <Route index element={<UploadPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="documents/:id" element={<ReportPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route element={<StaffRoute />}>
                <Route path="admin/documents" element={<AdminDocumentsPage />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
