import { useQuery } from '@tanstack/react-query'
import { ShieldCheck, CreditCard, FileText, Users, Calendar, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'
import { usePortalAuth } from '../../store/portalAuthStore'
import { Link } from 'react-router-dom'

const METHOD_LABELS: Record<string, string> = {
  bank_transfer: 'Bank Transfer', card: 'Card', cash: 'Cash',
  cheque: 'Cheque', upi: 'UPI', wallet: 'Wallet', net_banking: 'Net Banking',
}

const CLAIM_STATUS_COLORS: Record<string, string> = {
  submitted: 'bg-amber-100 text-amber-700',
  under_review: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  paid: 'bg-emerald-100 text-emerald-700',
  closed: 'bg-gray-100 text-gray-600',
}

function fmt(n: number | string) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function daysUntil(dateStr: string) {
  const diff = new Date(dateStr).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

export default function PortalDashboardPage() {
  const { user } = usePortalAuth()
  const policyQ = useQuery({ queryKey: ['portal-policy'], queryFn: portalCustomerApi.getPolicy, retry: false })
  const paymentsQ = useQuery({ queryKey: ['portal-payments'], queryFn: portalCustomerApi.getPayments, retry: false })
  const claimsQ = useQuery({ queryKey: ['portal-claims'], queryFn: portalCustomerApi.getClaims, retry: false })
  const membersQ = useQuery({ queryKey: ['portal-members'], queryFn: portalCustomerApi.getMembers, retry: false })

  const policy = policyQ.data?.data?.data
  const paymentsData = paymentsQ.data?.data?.data
  const payments: Record<string, unknown>[] = paymentsData?.payments ?? []
  const claims: Record<string, unknown>[] = claimsQ.data?.data?.data ?? []
  const members: Record<string, unknown>[] = membersQ.data?.data?.data ?? []

  const totalPaid = paymentsData?.total_paid ?? 0
  const recentPayments = payments.slice(0, 3)
  const recentClaims = claims.slice(0, 3)
  const activeClaims = claims.filter((c) => !['closed', 'rejected', 'paid'].includes(String(c.status))).length

  const expiryDays = policy?.expiry_date ? daysUntil(String(policy.expiry_date)) : null

  return (
    <div className="p-8">
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user?.first_name}!</h1>
        <p className="text-gray-500 text-sm mt-1">Here's a summary of your health coverage.</p>
      </div>

      {/* Policy status banner */}
      {policy && (
        <div className={`mb-6 flex items-center justify-between px-5 py-4 rounded-xl border ${
          policy.status === 'active' ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'
        }`}>
          <div className="flex items-center gap-3">
            {policy.status === 'active'
              ? <CheckCircle className="w-5 h-5 text-emerald-600" />
              : <AlertCircle className="w-5 h-5 text-amber-600" />}
            <div>
              <p className="font-semibold text-gray-900 text-sm">Policy {String(policy.policy_number)}</p>
              <p className="text-xs text-gray-500">{String(policy.product_name)} · {String(policy.plan_name)}</p>
            </div>
          </div>
          <div className="text-right">
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${
              policy.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
            }`}>{String(policy.status)}</span>
            {expiryDays !== null && expiryDays <= 60 && (
              <p className="text-xs text-amber-600 mt-1 font-medium">
                {expiryDays > 0 ? `Expires in ${expiryDays} days` : 'Expired'}
              </p>
            )}
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
          <div className="p-3 bg-emerald-100 rounded-xl"><ShieldCheck className="w-5 h-5 text-emerald-600" /></div>
          <div>
            <p className="text-xl font-bold text-gray-900 capitalize">{policy?.status ?? '—'}</p>
            <p className="text-xs text-gray-500">Policy Status</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-xl"><CreditCard className="w-5 h-5 text-blue-600" /></div>
          <div>
            <p className="text-xl font-bold text-gray-900">AED {fmt(totalPaid)}</p>
            <p className="text-xs text-gray-500">Total Paid</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
          <div className="p-3 bg-amber-100 rounded-xl"><FileText className="w-5 h-5 text-amber-600" /></div>
          <div>
            <p className="text-xl font-bold text-gray-900">{activeClaims}</p>
            <p className="text-xs text-gray-500">Active Claims</p>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
          <div className="p-3 bg-violet-100 rounded-xl"><Users className="w-5 h-5 text-violet-600" /></div>
          <div>
            <p className="text-xl font-bold text-gray-900">{members.length || (policy?.member_count ?? '—')}</p>
            <p className="text-xs text-gray-500">Members Covered</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Recent payments */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-gray-400" /> Recent Payments
            </h2>
            <Link to="/portal/payments" className="text-xs text-emerald-600 hover:text-emerald-700 font-medium">View all</Link>
          </div>
          {recentPayments.length === 0
            ? <p className="text-sm text-gray-400">No payments recorded yet.</p>
            : <div className="space-y-3">
              {recentPayments.map((p) => (
                <div key={String(p.id)} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-800">AED {fmt(String(p.amount))}</p>
                    <p className="text-xs text-gray-400">{METHOD_LABELS[String(p.method)] ?? String(p.method)}</p>
                  </div>
                  <p className="text-xs text-gray-400">{p.paid_at ? new Date(String(p.paid_at)).toLocaleDateString() : '—'}</p>
                </div>
              ))}
            </div>}
        </div>

        {/* Recent claims */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <FileText className="w-4 h-4 text-gray-400" /> Recent Claims
            </h2>
            <Link to="/portal/claims" className="text-xs text-emerald-600 hover:text-emerald-700 font-medium">View all</Link>
          </div>
          {recentClaims.length === 0
            ? <p className="text-sm text-gray-400">No claims filed yet.</p>
            : <div className="space-y-3">
              {recentClaims.map((c) => (
                <div key={String(c.id)} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-mono text-gray-700">{String(c.claim_number)}</p>
                    <p className="text-xs text-gray-400 capitalize">{String(c.claim_type).replace(/_/g, ' ')}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${CLAIM_STATUS_COLORS[String(c.status)] ?? 'bg-gray-100 text-gray-600'}`}>
                    {String(c.status).replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
            </div>}
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { to: '/portal/claims', label: 'File a Claim', icon: FileText, color: 'text-amber-600 bg-amber-50 hover:bg-amber-100' },
            { to: '/portal/policy', label: 'View Coverage', icon: ShieldCheck, color: 'text-emerald-600 bg-emerald-50 hover:bg-emerald-100' },
            { to: '/portal/documents', label: 'Download Docs', icon: Calendar, color: 'text-blue-600 bg-blue-50 hover:bg-blue-100' },
            { to: '/portal/members', label: 'View Members', icon: Users, color: 'text-violet-600 bg-violet-50 hover:bg-violet-100' },
          ].map(({ to, label, icon: Icon, color }) => (
            <Link key={to} to={to}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl text-center transition-colors ${color}`}>
              <Icon className="w-5 h-5" />
              <span className="text-xs font-medium">{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
