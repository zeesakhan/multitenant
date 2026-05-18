import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ShieldCheck, BadgeCheck, Plus, DollarSign, CreditCard, FileDown, RefreshCw, FileText } from 'lucide-react'
import { policiesApi, paymentsApi } from '../services/api'
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
  { value: 'upi', label: 'UPI' },
  { value: 'net_banking', label: 'Net Banking' },
]

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    active:    'bg-green-100 text-green-700',
    inactive:  'bg-gray-100 text-gray-500',
    expired:   'bg-red-100 text-red-600',
    cancelled: 'bg-orange-100 text-orange-600',
    suspended: 'bg-yellow-100 text-yellow-700',
    lapsed:    'bg-red-100 text-red-500',
    renewed:   'bg-blue-100 text-blue-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

function paymentMethodBadge(method: string) {
  const labels: Record<string, string> = {
    bank_transfer: 'Bank Transfer', card: 'Card', cash: 'Cash',
    cheque: 'Cheque', upi: 'UPI', wallet: 'Wallet', net_banking: 'Net Banking',
  }
  return (
    <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
      {labels[method] ?? method}
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
            <label className="label">Amount <span className="text-red-500">*</span></label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
              <input className="input pl-7" type="number" min="0.01" step="0.01"
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

// ── Policy Detail Modal ────────────────────────────────────────────────────────

function PolicyDetailModal({ policyId, onClose }: { policyId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [showPayment, setShowPayment] = useState(false)
  const [docError, setDocError] = useState('')
  const [renewError, setRenewError] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['policy', policyId],
    queryFn: () => policiesApi.get(policyId),
  })
  const { data: paymentsData, isLoading: paymentsLoading } = useQuery({
    queryKey: ['policy-payments', policyId],
    queryFn: () => paymentsApi.listByPolicy(policyId),
  })
  const { data: docsData, isLoading: docsLoading } = useQuery({
    queryKey: ['policy-documents', policyId],
    queryFn: () => policiesApi.listDocuments(policyId),
  })

  const policy: Policy | undefined = data?.data?.data
  const payments: Payment[] = paymentsData?.data?.data ?? []
  const documents: { id: string; file_name: string; mime_type: string; created_at: string }[] = docsData?.data?.data ?? []
  const totalCollected = payments
    .filter((p) => p.status === 'success')
    .reduce((s, p) => s + Number(p.amount), 0)

  const generateDocMut = useMutation({
    mutationFn: () => policiesApi.generateDocument(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policy-documents', policyId] })
      toast('Document generated.', 'info')
      setDocError('')
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
      setDocError(d?.errors?.[0]?.message ?? d?.detail ?? 'Failed to generate document.')
    },
  })

  const renewMut = useMutation({
    mutationFn: () => policiesApi.renew(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      queryClient.invalidateQueries({ queryKey: ['policy', policyId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      toast('Policy renewed.')
      setRenewError('')
      onClose()
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
      setRenewError(d?.errors?.[0]?.message ?? d?.detail ?? 'Failed to renew policy.')
    },
  })

  return (
    <>
      <Modal open={true} onClose={onClose} title="Policy Details" size="lg">
        {isLoading && <LoadingSpinner />}
        {policy && (
          <div className="space-y-5">
            {/* Policy number hero */}
            <div className="flex flex-col items-center py-5 bg-gradient-to-br from-violet-50 to-blue-50 rounded-xl border border-violet-100">
              <BadgeCheck className="w-10 h-10 text-violet-500 mb-2" />
              <p className="text-xs text-gray-500 mb-1">Policy Number</p>
              <p className="text-2xl font-bold font-mono text-gray-900">{policy.policy_number}</p>
              <div className="mt-2">{statusBadge(policy.status)}</div>
            </div>

            {/* Details grid */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              {([
                ['Customer', policy.customer_name],
                ['Email', policy.customer_email],
                ['Members', String(policy.member_count)],
                ['Premium', `$${Number(policy.total_premium).toFixed(2)}/mo`],
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

            {/* Payments section */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                  <DollarSign className="w-4 h-4 text-gray-400" /> Payments
                  {payments.length > 0 && (
                    <span className="text-xs font-normal text-gray-400 ml-1">
                      · ${totalCollected.toFixed(2)} collected
                    </span>
                  )}
                </p>
                {policy.status === 'active' && (
                  <button onClick={() => setShowPayment(true)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Record Payment
                  </button>
                )}
              </div>

              {paymentsLoading && <LoadingSpinner />}

              {!paymentsLoading && payments.length === 0 && (
                <div className="py-6 text-center border border-dashed border-gray-200 rounded-lg">
                  <CreditCard className="w-6 h-6 text-gray-300 mx-auto mb-2" />
                  <p className="text-xs text-gray-400">No payments recorded yet</p>
                </div>
              )}

              {payments.length > 0 && (
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
                          <td className="px-3 py-2 font-semibold text-gray-900">${Number(p.amount).toFixed(2)}</td>
                          <td className="px-3 py-2">{paymentMethodBadge(p.method)}</td>
                          <td className="px-3 py-2 text-gray-500">
                            {new Date(p.paid_at).toLocaleDateString()}
                          </td>
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

            {/* Documents */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-gray-400" /> Documents
                </p>
                <button onClick={() => generateDocMut.mutate()} disabled={generateDocMut.isPending}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                  <FileDown className="w-3 h-3" />
                  {generateDocMut.isPending ? 'Generating...' : 'Generate Policy Document'}
                </button>
              </div>
              {docError && <p className="text-xs text-red-600 mb-2">{docError}</p>}
              {docsLoading && <LoadingSpinner />}
              {!docsLoading && documents.length === 0 && (
                <div className="py-4 text-center border border-dashed border-gray-200 rounded-lg">
                  <p className="text-xs text-gray-400">No documents generated yet</p>
                </div>
              )}
              {documents.length > 0 && (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div key={doc.id} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-xs font-medium text-gray-800">{doc.file_name}</p>
                        <p className="text-xs text-gray-400">{new Date(doc.created_at).toLocaleDateString()}</p>
                      </div>
                      <a
                        href={policiesApi.downloadDocumentUrl(policyId, doc.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                      >
                        <FileDown className="w-3 h-3" /> Download
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Renew */}
            {policy && ['active', 'expired'].includes(policy.status) && (
              <div className="border-t border-gray-200 pt-4">
                {renewError && <p className="text-xs text-red-600 mb-2">{renewError}</p>}
                <button onClick={() => renewMut.mutate()} disabled={renewMut.isPending}
                  className="btn-secondary w-full justify-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  {renewMut.isPending ? 'Renewing...' : 'Renew Policy (+ 1 year)'}
                </button>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button onClick={onClose} className="btn-secondary">Close</button>
            </div>
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

export default function PoliciesPage() {
  const [viewingId, setViewingId] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesApi.list(1),
  })

  const policies: Policy[] = data?.data?.data ?? data?.data?.items ?? []

  const activeCount = policies.filter((p) => p.status === 'active').length
  const monthlyPremium = policies
    .filter((p) => p.status === 'active')
    .reduce((s, p) => s + Number(p.total_premium), 0)

  return (
    <div className="p-8">
      <PageHeader title="Policies" subtitle="Issued insurance policies" />

      {policies.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Total Policies', value: policies.length, color: 'text-gray-900' },
            { label: 'Active', value: activeCount, color: 'text-green-700' },
            { label: 'Monthly Premium', value: `$${monthlyPremium.toFixed(2)}`, color: 'text-violet-700' },
          ].map(({ label, value, color }) => (
            <div key={label} className="card py-4 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load policies." />}

      {!isLoading && !error && policies.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <ShieldCheck className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No policies yet</h3>
          <p className="text-sm text-gray-500 max-w-sm">
            Approve an application and click "Issue Policy" to generate your first policy.
          </p>
        </div>
      )}

      {!isLoading && !error && policies.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Policy #', 'Customer', 'Email', 'Premium', 'Status', 'Effective', 'Expires', 'Actions'].map((h) => (
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
                  <td className="px-4 py-3 text-gray-600">{p.customer_email}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    ${Number(p.total_premium).toFixed(2)}
                    <span className="text-xs text-gray-400 font-normal">/mo</span>
                  </td>
                  <td className="px-4 py-3">{statusBadge(p.status)}</td>
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
