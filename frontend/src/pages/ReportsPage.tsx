import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart2, TrendingUp, FileText, AlertCircle, Download, ShieldAlert, Globe, DollarSign } from 'lucide-react'
import { reportsApi } from '../services/api'
import api from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import { ReportSummary } from '../types'

function fmt(n: number) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function KpiCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="card py-5 text-center">
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      <p className="text-sm text-gray-600 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

function MiniBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{label}</span>
        <span className="font-medium">{value}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

const APP_STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-400', submitted: 'bg-amber-400',
  approved: 'bg-green-500', rejected: 'bg-red-400',
  issued: 'bg-violet-500', cancelled: 'bg-orange-400',
}

async function downloadReport(endpoint: string, filename: string, format: 'csv' | 'pdf' = 'csv') {
  try {
    const res = await api.get(`/reports/${endpoint}?format=${format}`, {
      responseType: format === 'pdf' ? 'blob' : 'text',
    })
    const mime = format === 'pdf' ? 'application/pdf' : 'text/csv'
    const blob = new Blob([res.data], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    alert('Failed to download report. Ensure the backend is running.')
  }
}

const EXTRA_REPORTS = [
  { key: 'policies-issued', label: 'Policy Issued Report', icon: ShieldAlert, color: 'text-violet-600', desc: 'All policies issued within date range' },
  { key: 'commission-statement', label: 'Commission Statement', icon: DollarSign, color: 'text-emerald-600', desc: 'Broker/insurer commission breakdown' },
  { key: 'underwriter', label: 'Underwriter Report', icon: FileText, color: 'text-blue-600', desc: 'Applications reviewed with UW loadings' },
  { key: 'aml-screening', label: 'AML Screening Report', icon: ShieldAlert, color: 'text-red-600', desc: 'AML risk scores and hold history' },
  { key: 'govt-verification', label: 'Govt Verification Report', icon: Globe, color: 'text-amber-600', desc: 'ICP, sanctions checks with results' },
  { key: 'str-log', label: 'STR Log Report', icon: AlertCircle, color: 'text-orange-600', desc: 'All Suspicious Transaction Reports' },
  { key: 'dha-fines', label: 'DHA Fine Report', icon: AlertCircle, color: 'text-rose-600', desc: 'Potential DHA fine exposure report' },
]

export default function ReportsPage() {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const summaryQ = useQuery({ queryKey: ['report-summary'], queryFn: () => reportsApi.summary() })
  const appsQ = useQuery({ queryKey: ['report-apps'], queryFn: () => reportsApi.applications(6) })
  const premiumQ = useQuery({ queryKey: ['report-premium'], queryFn: () => reportsApi.premium(6) })
  const claimsQ = useQuery({ queryKey: ['report-claims'], queryFn: () => reportsApi.claims(6) })

  const summary: ReportSummary | undefined = summaryQ.data?.data?.data
  const appRows: Record<string, unknown>[] = appsQ.data?.data?.data ?? []
  const premiumRows: { month: string; collected: number; payments: number }[] = premiumQ.data?.data?.data ?? []
  const claimRows: Record<string, unknown>[] = claimsQ.data?.data?.data ?? []

  const loading = summaryQ.isLoading || appsQ.isLoading || premiumQ.isLoading || claimsQ.isLoading

  if (loading) return <div className="p-8"><LoadingSpinner /></div>

  const maxAppTotal = Math.max(...appRows.map((r) => Number(r.total ?? 0)), 1)
  const maxPremium = Math.max(...premiumRows.map((r) => r.collected), 1)
  const maxClaimTotal = Math.max(...claimRows.map((r) => Number(r.total ?? 0)), 1)

  return (
    <div className="p-8">
      <PageHeader title="Reports" subtitle="Business performance and analytics" />

      {/* Summary KPIs */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KpiCard label="Active Policies" value={summary.active_policies} color="text-violet-700" />
          <KpiCard label="Expiring (30d)" value={summary.expiring_soon_30d} color="text-orange-600"
            sub="need renewal" />
          <KpiCard label="Pending Applications" value={summary.pending_applications} color="text-amber-600" />
          <KpiCard label="Open Claims" value={summary.open_claims} color="text-red-600" />
        </div>
      )}

      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <KpiCard label="Monthly Premium Due" value={`AED AED {fmt(summary.monthly_premium_due)}`} color="text-gray-900" />
          <KpiCard label="Collected This Month" value={`AED AED {fmt(summary.collected_this_month)}`} color="text-green-700" />
          <KpiCard label="Claims Paid This Month" value={`AED AED {fmt(summary.claims_paid_this_month)}`} color="text-blue-700" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Applications by month */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-400" /> Applications (last 6 months)
          </h2>
          {appRows.length === 0
            ? <p className="text-sm text-gray-400">No data yet.</p>
            : (
              <div className="space-y-4">
                {appRows.map((row) => (
                  <div key={String(row.month)} className="space-y-1.5">
                    <p className="text-xs font-medium text-gray-700">{String(row.month)}</p>
                    {['submitted', 'approved', 'issued', 'rejected'].map((s) => {
                      const val = Number((row as Record<string, unknown>)[s] ?? 0)
                      if (val === 0) return null
                      return <MiniBar key={s} label={s} value={val} max={maxAppTotal} color={APP_STATUS_COLORS[s] ?? 'bg-gray-400'} />
                    })}
                  </div>
                ))}
              </div>
            )}
        </div>

        {/* Premium collected by month */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gray-400" /> Premium Collected (last 6 months)
          </h2>
          {premiumRows.length === 0
            ? <p className="text-sm text-gray-400">No payments recorded yet.</p>
            : (
              <div className="space-y-3">
                {premiumRows.map((row) => (
                  <div key={row.month}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>{row.month}</span>
                      <span className="font-semibold text-emerald-700">AED {fmt(row.collected)}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div className="h-2 rounded-full bg-emerald-500"
                        style={{ width: `${Math.round((row.collected / maxPremium) * 100)}%` }} />
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{row.payments} payment{row.payments !== 1 ? 's' : ''}</p>
                  </div>
                ))}
              </div>
            )}
        </div>

        {/* Claims by month */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-gray-400" /> Claims (last 6 months)
          </h2>
          {claimRows.length === 0
            ? <p className="text-sm text-gray-400">No claims filed yet.</p>
            : (
              <div className="space-y-4">
                {claimRows.map((row) => (
                  <div key={String(row.month)} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-gray-700">{String(row.month)}</span>
                      <span className="text-gray-500">AED {fmt(Number(row.total_claimed ?? 0))} claimed</span>
                    </div>
                    <MiniBar label={`${row.total} total`} value={Number(row.total ?? 0)} max={maxClaimTotal} color="bg-red-400" />
                  </div>
                ))}
              </div>
            )}
        </div>
      </div>

      {!summary && (
        <div className="card text-center py-12">
          <BarChart2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No report data available yet. Create policies and record payments to see analytics.</p>
        </div>
      )}

      {/* Additional reports */}
      <div className="mt-8">
        <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <Download className="w-4 h-4 text-gray-400" /> Export Reports
        </h2>
        <div className="mb-4 flex items-center gap-4">
          <div>
            <label className="label">Date From</label>
            <input type="date" className="input text-sm" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div>
            <label className="label">Date To</label>
            <input type="date" className="input text-sm" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {EXTRA_REPORTS.map(({ key, label, icon: Icon, color, desc }) => (
            <div key={key} className="card flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Icon className={`w-5 h-5 ${color}`} />
                <div>
                  <p className="text-sm font-medium text-gray-800">{label}</p>
                  <p className="text-xs text-gray-500">{desc}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    const q = dateFrom || dateTo ? `&date_from=${dateFrom}&date_to=${dateTo}` : ''
                    downloadReport(`${key}?${q}`, `${key}.csv`, 'csv')
                  }}
                  className="text-xs text-gray-600 hover:text-gray-800 font-medium flex items-center gap-1 border border-gray-300 rounded px-2 py-1"
                >
                  <Download className="w-3 h-3" /> CSV
                </button>
                <button
                  onClick={() => {
                    const q = dateFrom || dateTo ? `&date_from=${dateFrom}&date_to=${dateTo}` : ''
                    downloadReport(`${key}?${q}`, `${key}.pdf`, 'pdf')
                  }}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 border border-primary-300 rounded px-2 py-1"
                >
                  <Download className="w-3 h-3" /> PDF
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
