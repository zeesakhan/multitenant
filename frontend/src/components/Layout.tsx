import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Building2, Package,
  FileText, ClipboardList, ShieldCheck, AlertCircle, BarChart2, LogOut, Shield, ChevronRight,
  CreditCard, UserCheck,
} from 'lucide-react'
import { clearAuth, useAuth } from '../store/authStore'
import { authApi } from '../services/api'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/tenants', label: 'Tenants', icon: Building2 },
  { to: '/users', label: 'Users', icon: Users },
  { to: '/products', label: 'Products', icon: Package },
  { to: '/quotations', label: 'Quotations', icon: ClipboardList },
  { to: '/applications', label: 'Applications', icon: FileText },
  { to: '/policies', label: 'Policies', icon: ShieldCheck },
  { to: '/members', label: 'Members', icon: UserCheck },
  { to: '/claims', label: 'Claims', icon: AlertCircle },
  { to: '/payments', label: 'Payments', icon: CreditCard },
  { to: '/reports', label: 'Reports', icon: BarChart2 },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    clearAuth()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-primary-900 text-white flex flex-col">
        <div className="p-6 border-b border-primary-700">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-primary-100" />
            <div>
              <p className="font-bold text-sm leading-tight">Health Insurance</p>
              <p className="text-xs text-primary-300">Platform</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to
            return (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  active
                    ? 'bg-primary-700 text-white'
                    : 'text-primary-200 hover:bg-primary-800 hover:text-white',
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
                {active && <ChevronRight className="w-3 h-3 ml-auto" />}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-primary-700">
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-xs font-bold">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.first_name} {user?.last_name}</p>
              <p className="text-xs text-primary-300 truncate">{user?.user_type}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-primary-200 hover:bg-primary-800 hover:text-white transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
