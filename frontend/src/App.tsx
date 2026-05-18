import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './store/authStore'
import { usePortalAuth } from './store/portalAuthStore'
import { ToastProvider } from './context/ToastContext'
import Layout from './components/Layout'
import PortalLayout from './components/PortalLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import TenantsPage from './pages/TenantsPage'
import UsersPage from './pages/UsersPage'
import ProductsPage from './pages/ProductsPage'
import QuotationsPage from './pages/QuotationsPage'
import ApplicationsPage from './pages/ApplicationsPage'
import PoliciesPage from './pages/PoliciesPage'
import ClaimsPage from './pages/ClaimsPage'
import ReportsPage from './pages/ReportsPage'
import MembersPage from './pages/MembersPage'
import PaymentsPage from './pages/PaymentsPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import NotFoundPage from './pages/NotFoundPage'
import PortalLoginPage from './pages/portal/PortalLoginPage'
import PortalRegisterPage from './pages/portal/PortalRegisterPage'
import PortalDashboardPage from './pages/portal/PortalDashboardPage'
import PortalPolicyPage from './pages/portal/PortalPolicyPage'
import PortalMembersPage from './pages/portal/PortalMembersPage'
import PortalClaimsPage from './pages/portal/PortalClaimsPage'
import PortalPaymentsPage from './pages/portal/PortalPaymentsPage'
import PortalDocumentsPage from './pages/portal/PortalDocumentsPage'
import PortalProfilePage from './pages/portal/PortalProfilePage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function PortalPrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = usePortalAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/portal/login" replace />
}

export default function App() {
  return (
    <ToastProvider>
    <Routes>
      {/* Staff portal */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/tenants" element={<TenantsPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/products" element={<ProductsPage />} />
                <Route path="/quotations" element={<QuotationsPage />} />
                <Route path="/applications" element={<ApplicationsPage />} />
                <Route path="/policies" element={<PoliciesPage />} />
                <Route path="/claims" element={<ClaimsPage />} />
                <Route path="/reports" element={<ReportsPage />} />
                <Route path="/members" element={<MembersPage />} />
                <Route path="/payments" element={<PaymentsPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />

      {/* Customer portal */}
      <Route path="/portal/login" element={<PortalLoginPage />} />
      <Route path="/portal/register" element={<PortalRegisterPage />} />
      <Route
        path="/portal/*"
        element={
          <PortalPrivateRoute>
            <PortalLayout>
              <Routes>
                <Route path="dashboard" element={<PortalDashboardPage />} />
                <Route path="policy" element={<PortalPolicyPage />} />
                <Route path="members" element={<PortalMembersPage />} />
                <Route path="claims" element={<PortalClaimsPage />} />
                <Route path="payments" element={<PortalPaymentsPage />} />
                <Route path="documents" element={<PortalDocumentsPage />} />
                <Route path="profile" element={<PortalProfilePage />} />
                <Route path="" element={<Navigate to="dashboard" replace />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </PortalLayout>
          </PortalPrivateRoute>
        }
      />
    </Routes>
    </ToastProvider>
  )
}
