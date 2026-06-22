import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ShieldCheck, BadgeCheck, Plus, DollarSign, CreditCard, FileDown,
  RefreshCw, FileText, Download, MessageSquare,
} from 'lucide-react'
import { policiesApi, paymentsApi, applicationsApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'
import { Policy, Payment } from '../types'

const METHOD_OPTIONS = [
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Card' },
  { value: 'cash', label: 'Cash' },
  { value: 'cheque', label: 'Cheque' },
]

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    inactive: 'bg-gray-100 text-gray-500',
    expired: 'bg-red-100 text-red-600',
    cancelled: 'bg-orange-100 text-orange-600',
    suspended: 'bg-yellow-100 text-yellow-700',
    lapsed: 'bg-red-100 text-red-500',
    renewed: 'bg-blue-100 text-blue-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

function AmlBadge({ status }: { status?: string }) {
  if (!status || status === 'clear') return null
  const styles: Record<string, string> = {
    flagged: 'bg-orange-100 text-orange-700',
    hold: 'bg-red-100 text-red-700',
    cleared: 'bg-green-100 text-green-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      AML {status}
    </span>
  )
}

function errMsg(err: unknown) {
  const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
  return d?.errors?.[0]?.message ?? d?.detail ?? 'Something went wrong.'
}

// ── Record Payment Modal ───────────────────────────────────────────────────────

function RecordPaymentModal({ open, onClose, policyId, defaultAmount }: {
  open: boolean; onClose: () => void; policyId: string; defaultAmount: string
}) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [form, setForm] = useState({ amount: defaultAmount, method: 'bank_transfer', reference: '', notes: '' })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => paymentsApi.record(policyId, {
      amount: parseFloat(form.amount),
      method: form.method,
      reference: form.reference || null,
      notes: form.notes || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policy-payments', policyId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast('Payment recorded.')
      onClose()
      setForm({ amount: defaultAmount, method: 'bank_transfer', reference: '', notes: '' })
      setError('')
    },
    onError: (err: unknown) => setError(errMsg(err)),
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title="Record Payment" level={2}>
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Amount (AED) <span className="text-red-500">*</span></label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">AED</span>
              <input className="input pl-12" type="number" min="0.01" step="0.01"
                value={form.amount} onChange={set('amount')} required />
            </div>
          </div>
          <div>
            <label className="label">Method <span className="text-red-500">*</span></label>
            <select className="input" value={form.method} onChange={set('method')}>
              {METHOD_OPTIONS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Reference / Transaction ID</label>
          <input className="input" value={form.reference} onChange={set('reference')} placeholder="Optional reference number" />
        </div>
        <div>
          <label className="label">Notes</label>
          <input className="input" value={form.notes} onChange={set('notes')} placeholder="Optional notes" />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Recording...' : 'Record Payment'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ── Policy Detail Modal (4-tab) ────────────────────────────────────────────────

function PolicyDetailModal({ policyId, onClose }: { policyId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [showPayment, setShowPayment] = useState(false)
  const [renewError, setRenewError] = useState('')
  const [activeTab, setActiveTab] = useState<'personal' | 'signed' | 'other' | 'remarks'>('personal')
  const [remarkText, setRemarkText] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['policy', policyId],
    queryFn: () => policiesApi.get(policyId),
  })
  const { data: paymentsData } = useQuery({
    queryKey: ['policy-payments', policyId],
    queryFn: () => paymentsApi.listByPolicy(policyId),
  })
  const { data: docsData } = useQuery({
    queryKey: ['policy-documents', policyId],
    queryFn: () => policiesApi.listDocuments(policyId),
  })

  const policy: Policy | undefined = data?.data?.data
  const payments: Payment[] = paymentsData?.data?.data ?? []
  const documents: { id: string; file_name: string; mime_type: string; created_at: string }[] = docsData?.data?.data ?? []

  const renewMut = useMutation({
    mutationFn: () => policiesApi.renew(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      queryClient.invalidateQueries({ queryKey: ['policy', policyId] })
      toast('Policy renewed.')
      setRenewError('')
      onClose()
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
      setRenewError(d?.errors?.[0]?.message ?? d?.detail ?? 'Failed to renew policy.')
    },
  })

  // Get remarks from the linked application
  const { data: remarkData } = useQuery({
    queryKey: ['policy-remarks', policyId],
    queryFn: async () => {
      const pData = data?.data?.data
      if (!pData?.application_id) return { data: { data: [] } }
      return applicationsApi.listRemarks(pData.application_id)
    },
    enabled: !!policy?.application_id,
  })

  const remarks: Array<{ text: string; author: string; author_type: string; created_at: string }> =
    remarkData?.data?.data ?? []

  const addRemark = useMutation({
    mutationFn: () => applicationsApi.addRemark((policy as unknown as { application_id: string }).application_id, remarkText),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policy-remarks', policyId] })
      toast('Remark added.')
      setRemarkText('')
    },
  })

  async function downloadPdf(
    fetchFn: () => Promise<{ data: Blob }>,
    filename: string,
  ) {
    try {
      const res = await fetchFn()
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      toast('Failed to generate document.')
    }
  }

  const tabs = [
    { id: 'personal', label: 'Personal Details' },
    { id: 'signed', label: 'Signed Docs' },
    { id: 'other', label: 'Other Documents' },
    { id: 'remarks', label: 'Remarks' },
  ] as const

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = {
      underwriter: 'bg-purple-100 text-purple-700',
      broker: 'bg-blue-100 text-blue-700',
      compliance_officer: 'bg-red-100 text-red-700',
      admin: 'bg-gray-100 text-gray-700',
      system: 'bg-amber-100 text-amber-700',
    }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${colors[role] ?? 'bg-gray-100 text-gray-600'}`}>
        {role?.replace(/_/g, ' ') ?? 'Staff'}
      </span>
    )
  }

  const signedDocs = [
    { label: 'Medical Application Form (MAF)', fn: () => policiesApi.generateSchedule(policyId), file: `MAF-${policyId}.pdf` },
    { label: 'KYC Document', fn: () => policiesApi.generateSchedule(policyId), file: `KYC-${policyId}.pdf` },
    { label: 'Table of Benefits (ToB)', fn: () => policiesApi.generateSchedule(policyId), file: `TOB-${policyId}.pdf` },
  ]

  const otherDocs = [
    { label: 'Policy Schedule', fn: () => policiesApi.generateSchedule(policyId), file: `SCH-${policyId}.pdf` },
    { label: 'Credit Note', fn: () => policiesApi.generateCreditNote(policyId), file: `CN-${policyId}.pdf` },
    { label: 'Tax Invoice', fn: () => policiesApi.generateTaxInvoice(policyId), file: `INV-${policyId}.pdf` },
    { label: 'Receipt Voucher', fn: () => policiesApi.generateReceipt(policyId), file: `RV-${policyId}.pdf` },
  ]

  return (
    <>
      <Modal open={true} onClose={onClose} title="Policy Details" size="lg">
        {isLoading && <LoadingSpinner />}
        {policy && (
          <div className="space-y-4">
            {/* Hero */}
            <div className="flex flex-col items-center py-4 bg-gradient-to-br from-violet-50 to-blue-50 rounded-xl border border-violet-100">
              <BadgeCheck className="w-8 h-8 text-violet-500 mb-1" />
              <p className="text-xs text-gray-500">Policy Number</p>
              <p className="text-xl font-bold font-mono text-gray-900">{policy.policy_number}</p>
              <div className="mt-1 flex gap-2">
                {statusBadge(policy.status)}
                {(policy as unknown as { aml_status?: string }).aml_status &&
                  <AmlBadge status={(policy as unknown as { aml_status?: string }).aml_status} />}
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-200">
              {tabs.map((t) => (
                <button key={t.id} onClick={() => setActiveTab(t.id)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === t.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}>
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab: Personal Details */}
            {activeTab === 'personal' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {([
                    ['Customer', policy.customer_name],
                    ['Email', policy.customer_email],
                    ['Members', String(policy.member_count)],
                    ['Premium', `AED ${Number(policy.total_premium).toFixed(2)}`],
                    ['Effective', new Date(policy.effective_date).toLocaleDateString()],
                    ['Expiry', new Date(policy.expiry_date).toLocaleDateString()],
                    ['Issued', policy.issued_at ? new Date(policy.issued_at).toLocaleDateString() : '—'],
                    ['Created', new Date(policy.created_at).toLocaleDateString()],
                  ] as [string, string][]).map(([label, value]) => (
                    <div key={label} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">{label}</p>
                      <p className="font-medium text-gray-900">{value}</p>
                    </div>
                  ))}
                </div>

                {/* Payments */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                      <DollarSign className="w-4 h-4 text-gray-400" /> Payments
                    </p>
                    {policy.status === 'active' && (
                      <button onClick={() => setShowPayment(true)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                        <Plus className="w-3 h-3" /> Record Payment
                      </button>
                    )}
                  </div>
                  {payments.length === 0 ? (
                    <div className="py-4 text-center border border-dashed border-gray-200 rounded-lg">
                      <p className="text-xs text-gray-400">No payments recorded yet</p>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-gray-200 overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-50">
                          <tr>
                            {['Ref #', 'Amount', 'Method', 'Date', 'Status'].map((h) => (
                              <th key={h} className="text-left px-3 py-2 font-medium text-gray-600">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {payments.map((p) => (
                            <tr key={p.id} className="hover:bg-gray-50">
                              <td className="px-3 py-2 font-mono text-gray-600">{p.payment_number}</td>
                              <td className="px-3 py-2 font-semibold text-gray-900">AED {Number(p.amount).toFixed(2)}</td>
                              <td className="px-3 py-2 capitalize">{p.method?.replace(/_/g, ' ')}</td>
                              <td className="px-3 py-2 text-gray-500">{new Date(p.paid_at).toLocaleDateString()}</td>
                              <td className="px-3 py-2">
                                <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${
                                  p.status === 'success' ? 'bg-green-100 text-green-700'
                                    : p.status === 'failed' ? 'bg-red-100 text-red-600'
                                    : 'bg-gray-100 text-gray-600'
                                }`}>{p.status}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Renew */}
                {['active', 'expired'].includes(policy.status) && (
                  <div className="border-t border-gray-200 pt-4">
                    {renewError && <p className="text-xs text-red-600 mb-2">{renewError}</p>}
                    <button onClick={() => renewMut.mutate()} disabled={renewMut.isPending}
                      className="btn-secondary w-full justify-center gap-2">
                      <RefreshCw className="w-4 h-4" />
                      {renewMut.isPending ? 'Renewing...' : 'Renew Policy (+ 1 year)'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Signed Docs */}
            {activeTab === 'signed' && (
              <div className="space-y-3">
                <p className="text-sm text-gray-500">Application documents requiring signatures.</p>
                {signedDocs.map((d) => (
                  <div key={d.label} className="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-gray-400" />
                      <span className="text-sm font-medium text-gray-700">{d.label}</span>
                    </div>
                    <button
                      onClick={() => downloadPdf(d.fn, d.file)}
                      className="flex items-center gap-1.5 text-xs text-primary-600 hover:text-primary-700 font-medium"
                    >
                      <Download className="w-3.5 h-3.5" /> Download
                    </button>
                  </div>
                ))}
                {/* Uploaded documents */}
                {documents.length > 0 && (
                  <>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mt-3">Uploaded</p>
                    {documents.map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                        <p className="text-xs font-medium text-gray-800">{doc.file_name}</p>
                        <a href={policiesApi.downloadDocumentUrl(policyId, doc.id)}
                          target="_blank" rel="noopener noreferrer"
                          className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                          <FileDown className="w-3 h-3" /> Download
                        </a>
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}

            {/* Tab: Other Documents */}
            {activeTab === 'other' && (
              <div className="space-y-3">
                <p className="text-sm text-gray-500">Financial and policy documents.</p>
                {otherDocs.map((d) => (
                  <div key={d.label} className="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-primary-400" />
                      <span className="text-sm font-medium text-gray-700">{d.label}</span>
                    </div>
                    <button
                      onClick={() => downloadPdf(d.fn, d.file)}
                      className="flex items-center gap-1.5 text-xs text-primary-600 hover:text-primary-700 font-medium"
                    >
                      <Download className="w-3.5 h-3.5" /> Generate & Download
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Tab: Remarks */}
            {activeTab === 'remarks' && (
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-gray-400" /> Threaded Remarks
                </p>
                {remarks.length === 0 ? (
                  <p className="text-xs text-gray-400 italic mb-3">No remarks yet.</p>
                ) : (
                  <div className="space-y-2 mb-3 max-h-56 overflow-y-auto">
                    {remarks.map((r, i) => (
                      <div key={i} className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium text-gray-700">{r.author}</span>
                          {roleBadge(r.author_type)}
                          <span className="text-xs text-gray-400 ml-auto">{new Date(r.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-sm text-gray-700">{r.text}</p>
                      </div>
                    ))}
                  </div>
                )}
                {policy.application_id && (
                  <div className="flex gap-2">
                    <input className="input flex-1 text-sm" value={remarkText}
                      onChange={(e) => setRemarkText(e.target.value)} placeholder="Add a remark..." />
                    <button className="btn-primary text-sm px-3"
                      disabled={!remarkText.trim() || addRemark.isPending}
                      onClick={() => addRemark.mutate()}>
                      Add
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>

      {policy && (
        <RecordPaymentModal
          open={showPayment}
          onClose={() => setShowPayment(false)}
          policyId={policyId}
          defaultAmount={policy.total_premium}
        />
      )}
    </>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

const STATUS_FILTERS = [
  { label: 'All Status', value: '' },
  { label: 'Active', value: 'active' },
  { label: 'Expired', value: 'expired' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'Suspended', value: 'suspended' },
]

const AML_FILTERS = [
  { label: 'All AML', value: '' },
  { label: 'Clear', value: 'clear' },
  { label: 'Flagged', value: 'flagged' },
  { label: 'Hold', value: 'hold' },
]

export default function PoliciesPage() {
  const [viewingId, setViewingId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [amlFilter, setAmlFilter] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['policies', statusFilter, amlFilter],
    queryFn: () => policiesApi.list(1, {
      status: statusFilter || undefined,
      aml_status: amlFilter || undefined,
    }),
  })

  const allPolicies: Policy[] = data?.data?.data ?? data?.data?.items ?? []
  const policies = allPolicies.filter((p) =>
    !search || p.customer_name.toLowerCase().includes(search.toLowerCase())
      || p.policy_number.toLowerCase().includes(search.toLowerCase())
      || p.customer_email.toLowerCase().includes(search.toLowerCase()),
  )

  const activeCount = policies.filter((p) => p.status === 'active').length
  const monthlyPremium = policies
    .filter((p) => p.status === 'active')
    .reduce((s, p) => s + Number(p.total_premium), 0)

  return (
    <div className="p-8">
      <PageHeader title="Policies" subtitle="Issued insurance policies" />

      {allPolicies.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-5">
          {[
            { label: 'Total Policies', value: allPolicies.length, color: 'text-gray-900' },
            { label: 'Active', value: activeCount, color: 'text-green-700' },
            { label: 'Total Premium', value: `AED ${monthlyPremium.toFixed(2)}`, color: 'text-violet-700' },
          ].map(({ label, value, color }) => (
            <div key={label} className="card py-4 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filter bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input className="input w-56 text-sm" placeholder="Search by name or policy #..."
          value={search} onChange={(e) => setSearch(e.target.value)} />
        <select className="input w-36 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {STATUS_FILTERS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        <select className="input w-36 text-sm" value={amlFilter} onChange={(e) => setAmlFilter(e.target.value)}>
          {AML_FILTERS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        {(statusFilter || amlFilter || search) && (
          <button className="text-sm text-gray-500 hover:text-gray-700"
            onClick={() => { setStatusFilter(''); setAmlFilter(''); setSearch('') }}>
            Clear
          </button>
        )}
      </div>

      {/* Quick chips */}
      <div className="mb-5 flex flex-wrap gap-2">
        {[
          { label: 'Active', s: 'active', a: '' },
          { label: 'AML Hold', s: '', a: 'hold' },
          { label: 'AML Flagged', s: '', a: 'flagged' },
          { label: 'Expired', s: 'expired', a: '' },
        ].map((chip) => {
          const active = statusFilter === chip.s && amlFilter === chip.a
          return (
            <button key={chip.label}
              onClick={() => { setStatusFilter(chip.s); setAmlFilter(chip.a) }}
              className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                active
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
              }`}>
              {chip.label}
            </button>
          )
        })}
      </div>

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load policies." />}

      {!isLoading && !error && policies.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <ShieldCheck className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No policies found</h3>
          <p className="text-sm text-gray-500 max-w-sm">
            {statusFilter || amlFilter || search
              ? 'Try adjusting your filters.'
              : 'Approve an application and click "Issue Policy" to generate your first policy.'}
          </p>
        </div>
      )}

      {!isLoading && !error && policies.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Policy #', 'Customer', 'Email', 'Premium', 'Status', 'AML', 'Effective', 'Expires', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {policies.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <BadgeCheck className="w-4 h-4 text-violet-500 flex-shrink-0" />
                      <span className="font-mono text-xs font-semibold text-gray-800">{p.policy_number}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">{p.customer_name}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{p.customer_email}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    AED {Number(p.total_premium).toFixed(2)}
                  </td>
                  <td className="px-4 py-3">{statusBadge(p.status)}</td>
                  <td className="px-4 py-3">
                    <AmlBadge status={(p as unknown as { aml_status?: string }).aml_status} />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{new Date(p.effective_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{new Date(p.expiry_date).toLocaleDateString()}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => setViewingId(p.id)}
                      className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {viewingId && <PolicyDetailModal policyId={viewingId} onClose={() => setViewingId(null)} />}
    </div>
  )
}
