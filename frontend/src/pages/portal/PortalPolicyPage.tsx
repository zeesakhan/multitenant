import { useQuery } from '@tanstack/react-query'
import { ShieldCheck, Calendar, DollarSign, Package, Users } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'

const COVERAGE_TYPE_LABELS: Record<string, string> = {
  hospitalization: 'Hospitalization', outpatient: 'Outpatient', dental: 'Dental',
  vision: 'Vision', maternity: 'Maternity', mental_health: 'Mental Health',
  prescription: 'Prescription', preventive: 'Preventive', emergency: 'Emergency',
  wellness: 'Wellness',
}

function fmt(n: string | number) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const STATUS_COLORS: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700',
  expired: 'bg-red-100 text-red-700',
  suspended: 'bg-amber-100 text-amber-700',
  cancelled: 'bg-gray-100 text-gray-600',
}

export default function PortalPolicyPage() {
  const policyQ = useQuery({ queryKey: ['portal-policy'], queryFn: portalCustomerApi.getPolicy, retry: false })
  const coverageQ = useQuery({ queryKey: ['portal-coverage'], queryFn: portalCustomerApi.getCoverage, retry: false })

  const policy = policyQ.data?.data?.data
  const coverage: Record<string, unknown>[] = coverageQ.data?.data?.data ?? []

  if (policyQ.isLoading) return <div className="p-8 text-gray-500 text-sm">Loading policy…</div>

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">My Policy</h1>
        <p className="text-gray-500 text-sm mt-1">Your health insurance coverage details.</p>
      </div>

      {!policy ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-500">
          No policy data available.
        </div>
      ) : (
        <div className="space-y-6">
          {/* Policy overview card */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                  <ShieldCheck className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <p className="font-mono text-lg font-bold text-gray-900">{String(policy.policy_number)}</p>
                  <p className="text-sm text-gray-500">{String(policy.product_name)}</p>
                </div>
              </div>
              <span className={`text-sm font-semibold px-3 py-1 rounded-full capitalize ${STATUS_COLORS[String(policy.status)] ?? 'bg-gray-100 text-gray-600'}`}>
                {String(policy.status)}
              </span>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Package className="w-3 h-3" /> Plan</p>
                <p className="text-sm font-semibold text-gray-900">{String(policy.plan_name)}</p>
                <p className="text-xs text-gray-400 capitalize">{String(policy.plan_type ?? '')}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><DollarSign className="w-3 h-3" /> Premium</p>
                <p className="text-sm font-semibold text-gray-900">AED {fmt(String(policy.total_premium))}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Calendar className="w-3 h-3" /> Effective</p>
                <p className="text-sm font-semibold text-gray-900">
                  {policy.effective_date ? new Date(String(policy.effective_date)).toLocaleDateString() : '—'}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Calendar className="w-3 h-3" /> Expires</p>
                <p className="text-sm font-semibold text-gray-900">
                  {policy.expiry_date ? new Date(String(policy.expiry_date)).toLocaleDateString() : '—'}
                </p>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-100 grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-400 mb-1">Policyholder</p>
                <p className="text-sm font-medium text-gray-900">{String(policy.customer_name)}</p>
                <p className="text-xs text-gray-400">{String(policy.customer_email)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1 flex items-center gap-1"><Users className="w-3 h-3" /> Members covered</p>
                <p className="text-sm font-medium text-gray-900">{String(policy.member_count)}</p>
              </div>
            </div>
          </div>

          {/* Coverage breakdown */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Coverage Breakdown</h2>
            {coverageQ.isLoading ? (
              <p className="text-sm text-gray-400">Loading coverage…</p>
            ) : coverage.length === 0 ? (
              <p className="text-sm text-gray-400">No coverage items found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {['Coverage', 'Type', 'Limit', 'Co-pay', 'Premium', 'Status'].map((h) => (
                        <th key={h} className="text-left px-4 py-3 text-xs font-medium text-gray-600">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {coverage.map((item) => (
                      <tr key={String(item.id)} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-gray-900">{String(item.coverage_name ?? '—')}</td>
                        <td className="px-4 py-3 text-gray-600">
                          {COVERAGE_TYPE_LABELS[String(item.coverage_type ?? '')] ?? String(item.coverage_type ?? '—')}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {item.limit_amount ? `AED ${fmt(String(item.limit_amount))}` : '—'}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {item.copay ? `AED ${fmt(String(item.copay))}` : '—'}
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900">AED {fmt(String(item.premium))}</td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-full capitalize font-medium ${
                            item.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                          }`}>{String(item.status)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
