import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './store/authStore'
import { ToastProvider } from './context/ToastContext'
import Layout from './components/Layout'
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
import NotFoundPage from './pages/NotFoundPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <ToastProvider>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
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
    </Routes>
    </ToastProvider>
  )
}
