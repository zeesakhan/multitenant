import { useState, useRef, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, Building2, Package,
  FileText, ClipboardList, ShieldCheck, AlertCircle, BarChart2, LogOut, Shield, ChevronRight,
  CreditCard, UserCheck, Bell, ShieldAlert, Globe, FilePlus,
} from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clearAuth, useAuth } from '../store/authStore'
import { authApi, notificationsApi } from '../services/api'
import clsx from 'clsx'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/tenants', label: 'Tenants', icon: Building2 },
  { to: '/users', label: 'Users', icon: Users },
  { to: '/products', label: 'Products', icon: Package },
  { to: '/quotations', label: 'Quotations', icon: ClipboardList },
  { to: '/new-policy', label: 'New Policy', icon: FilePlus },
  { to: '/applications', label: 'Applications', icon: FileText },
  { to: '/policies', label: 'Policies', icon: ShieldCheck },
  { to: '/members', label: 'Members', icon: UserCheck },
  { to: '/claims', label: 'Claims', icon: AlertCircle },
  { to: '/payments', label: 'Payments', icon: CreditCard },
  { to: '/reports', label: 'Reports', icon: BarChart2 },
  { to: '/aml', label: 'AML', icon: ShieldAlert },
  { to: '/govt-checks', label: 'Govt Checks', icon: Globe },
]

interface NotificationItem {
  id: string
  title: string
  body: string
  is_read: boolean
  created_at: string
  notification_type: string
}

function NotificationBell() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list(),
    refetchInterval: 60_000,
  })

  const notifications: NotificationItem[] = data?.data?.data?.notifications ?? []
  const unreadCount: number = data?.data?.data?.unread_count ?? 0

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 rounded-lg text-primary-200 hover:bg-primary-800 hover:text-white transition-colors"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-white text-[10px] font-bold flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute bottom-full right-0 mb-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <p className="font-semibold text-gray-800 text-sm">Notifications</p>
            {unreadCount > 0 && (
              <button
                onClick={() => markAll.mutate()}
                className="text-xs text-primary-600 hover:text-primary-700 font-medium"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
            {notifications.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No notifications</p>
            ) : (
              notifications.slice(0, 15).map((n) => (
                <button
                  key={n.id}
                  onClick={() => { if (!n.is_read) markRead.mutate(n.id) }}
                  className={clsx(
                    'w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors',
                    !n.is_read && 'bg-blue-50',
                  )}
                >
                  <p className={clsx('text-sm', !n.is_read ? 'font-semibold text-gray-900' : 'text-gray-700')}>
                    {n.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.body}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

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

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
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
          <div className="flex items-center gap-2 px-3 py-2 mb-2">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
              {user?.first_name?.[0]}{user?.last_name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.first_name} {user?.last_name}</p>
              <p className="text-xs text-primary-300 truncate">{user?.user_type}</p>
            </div>
            <NotificationBell />
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
