import { useQuery } from '@tanstack/react-query'
import {
  Users, ShieldCheck, FileText, DollarSign,
  CheckCircle, Activity, TrendingUp, Clock,
} from 'lucide-react'
import { dashboardApi, healthApi } from '../services/api'
import { useAuth } from '../store/authStore'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusBadge from '../components/StatusBadge'
import { DashboardStats } from '../types'

function StatCard({
  label, value, sub, icon: Icon, color,
}: {
  label: string; value: string | number; sub?: string; icon: React.ElementType; color: string
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-xl ${color} flex-shrink-0`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

function fmt(n: number) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const METHOD_LABELS: Record<string, string> = {
  bank_transfer: 'Bank Transfer',
  card: 'Card',
  cash: 'Cash',
  cheque: 'Cheque',
  upi: 'UPI',
  wallet: 'Wallet',
  net_banking: 'Net Banking',
}

export default function DashboardPage() {
  const { user } = useAuth()

  const health = useQuery({ queryKey: ['health'], queryFn: () => healthApi.check(), retry: false })
  const statsQuery = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardApi.stats(),
    retry: false,
  })

  const backendOnline = health.isSuccess

  if (statsQuery.isLoading) return <div className="p-8"><LoadingSpinner /></div>

  const stats: DashboardStats | undefined = statsQuery.data?.data?.data
  const appStatuses = ['draft', 'submitted', 'approved', 'rejected', 'issued', 'cancelled']
  const statusColors: Record<string, string> = {
    draft: 'bg-gray-400',
    submitted: 'bg-amber-400',
    approved: 'bg-green-400',
    rejected: 'bg-red-400',
    issued: 'bg-violet-500',
    cancelled: 'bg-orange-400',
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Dashboard"
        subtitle={`Welcome back, ${user?.first_name ?? 'User'} · ${user?.user_type?.replace(/_/g, ' ')}`}
      />

      {/* Backend status */}
      <div className={`mb-6 flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium ${backendOnline ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
        {backendOnline
          ? <><CheckCircle className="w-4 h-4" /> Backend API is online</>
          : <><Activity className="w-4 h-4" /> Backend API is offline — start it with uvicorn</>}
      </div>

      {!stats && !statsQuery.isLoading && (
        <div className="card text-center py-8 text-gray-500 text-sm">
          Unable to load dashboard stats. Is the backend running?
        </div>
      )}

      {stats && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Active Policies"
              value={stats.policies.active}
              sub={`${stats.policies.total} total`}
              icon={ShieldCheck}
              color="bg-violet-500"
            />
            <StatCard
              label="Monthly Premium"
              value={`$${fmt(stats.policies.monthly_premium)}`}
              sub="from active policies"
              icon={TrendingUp}
              color="bg-emerald-500"
            />
            <StatCard
              label="Applications"
              value={stats.applications.total}
              sub={`${stats.applications.by_status['submitted'] ?? 0} pending review`}
              icon={FileText}
              color="bg-amber-500"
            />
            <StatCard
              label="Collected"
              value={`$${fmt(stats.payments.total_collected)}`}
              sub={`${stats.payments.total} payments`}
              icon={DollarSign}
              color="bg-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Applications by status */}
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-400" /> Applications by Status
              </h2>
              <div className="space-y-2.5">
                {appStatuses.map((s) => {
                  const count = stats.applications.by_status[s] ?? 0
                  const pct = stats.applications.total > 0
                    ? Math.round((count / stats.applications.total) * 100)
                    : 0
                  return (
                    <div key={s}>
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span className="capitalize">{s}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${statusColors[s] ?? 'bg-gray-400'}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Recent Applications */}
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" /> Recent Applications
              </h2>
              {stats.recent_applications.length === 0
                ? <p className="text-sm text-gray-400">No applications yet.</p>
                : (
                  <div className="space-y-3">
                    {stats.recent_applications.map((a) => (
                      <div key={a.id} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-800">{a.customer_name}</p>
                          <p className="text-xs text-gray-400 font-mono">{a.application_number}</p>
                        </div>
                        <StatusBadge status={a.status} />
                      </div>
                    ))}
                  </div>
                )}
            </div>

            {/* Recent Payments */}
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-gray-400" /> Recent Payments
              </h2>
              {stats.recent_payments.length === 0
                ? <p className="text-sm text-gray-400">No payments recorded yet.</p>
                : (
                  <div className="space-y-3">
                    {stats.recent_payments.map((p) => (
                      <div key={p.id} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-800">${fmt(p.amount)}</p>
                          <p className="text-xs text-gray-400">{METHOD_LABELS[p.method] ?? p.method}</p>
                        </div>
                        <p className="text-xs text-gray-400">
                          {new Date(p.paid_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </div>

          {/* Users + system status */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <Users className="w-4 h-4 text-gray-400" /> Team
              </h2>
              <div className="flex items-center gap-4">
                <div className="p-3 bg-violet-100 rounded-xl">
                  <Users className="w-6 h-6 text-violet-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{stats.users.total}</p>
                  <p className="text-sm text-gray-500">Active users in your tenant</p>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">System Status</h2>
              <div className="space-y-2.5">
                {[
                  { label: 'Backend API', status: backendOnline ? 'online' : 'offline' },
                  { label: 'Authentication', status: 'online' },
                  { label: 'Database (SQLite dev)', status: 'online' },
                  { label: 'Redis Cache', status: 'offline' },
                  { label: 'Celery Workers', status: 'offline' },
                ].map(({ label, status }) => (
                  <div key={label} className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0">
                    <span className="text-sm text-gray-700">{label}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${status === 'online' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
