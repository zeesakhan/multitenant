import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, ShieldCheck, Users, FileText,
  CreditCard, FolderOpen, User, LogOut, ChevronRight, Heart,
} from 'lucide-react'
import { clearPortalAuth, usePortalAuth } from '../store/portalAuthStore'
import clsx from 'clsx'

const navItems = [
  { to: '/portal/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/portal/policy', label: 'My Policy', icon: ShieldCheck },
  { to: '/portal/members', label: 'Covered Members', icon: Users },
  { to: '/portal/claims', label: 'Claims', icon: FileText },
  { to: '/portal/payments', label: 'Payments', icon: CreditCard },
  { to: '/portal/documents', label: 'Documents', icon: FolderOpen },
  { to: '/portal/profile', label: 'My Profile', icon: User },
]

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user } = usePortalAuth()

  const handleLogout = () => {
    clearPortalAuth()
    navigate('/portal/login')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-emerald-900 text-white flex flex-col">
        <div className="p-6 border-b border-emerald-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-emerald-500 rounded-xl flex items-center justify-center">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-sm leading-tight">Member Portal</p>
              <p className="text-xs text-emerald-300">Health Insurance</p>
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
                    ? 'bg-emerald-700 text-white'
                    : 'text-emerald-200 hover:bg-emerald-800 hover:text-white',
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
                {active && <ChevronRight className="w-3 h-3 ml-auto" />}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-emerald-700">
          <div className="flex items-center gap-3 px-3 py-2 mb-2">
            <div className="w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center text-xs font-bold">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.first_name} {user?.last_name}</p>
              <p className="text-xs text-emerald-300 truncate">Policyholder</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-emerald-200 hover:bg-emerald-800 hover:text-white transition-colors"
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
