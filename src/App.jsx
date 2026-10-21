import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import AppLayout from './layouts/AppLayout.jsx'
import AuthPage from './pages/AuthPage.jsx'
import ApplicationsPage from './pages/ApplicationsPage.jsx'
import InterviewsPage from './pages/InterviewsPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import PreparationPage from './pages/PreparationPage.jsx'
import ProjectHomePage from './pages/ProjectHomePage'
import WorkspacePage from './pages/WorkspacePage.jsx'
import './styles/workspace.css'

const DashboardPage = lazy(() => import('./pages/DashboardPage.jsx'))

function App() {
  return (
    <Routes>
      <Route path="/" element={<ProjectHomePage />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Suspense fallback={<main className="route-loading">Loading dashboard…</main>}>
                <DashboardPage />
              </Suspense>
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/applications"
        element={
          <ProtectedRoute>
            <AppLayout>
              <ApplicationsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/interviews"
        element={
          <ProtectedRoute>
            <AppLayout>
              <InterviewsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <AppLayout>
              <WorkspacePage section="Reports" />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/preparation"
        element={
          <ProtectedRoute>
            <AppLayout>
              <PreparationPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route path="/app" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
