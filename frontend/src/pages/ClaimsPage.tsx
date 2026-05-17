import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, AlertCircle, CheckCircle, XCircle, Clock, DollarSign } from 'lucide-react'
import { claimsApi, policiesApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { Claim, Policy } from '../types'

const CLAIM_TYPES = [
  { value: 'hospitalization', label: 'Hospitalization' },
  { value: 'outpatient', label: 'Outpatient' },
  { value: 'pharmacy', label: 'Pharmacy' },
  { value: 'dental', label: 'Dental' },
  { value: 'vision', label: 'Vision' },
  { value: 'maternity', label: 'Maternity' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'other', label: 'Other' },
]

function claimTypeBadge(type: string) {
  const colors: Record<string, string> = {
    hospitalization: 'bg-red-100 text-red-700',
    outpatient: 'bg-blue-100 text-blue-700',
    pharmacy: 'bg-green-100 text-green-700',
    dental: 'bg-yellow-100 text-yellow-700',
    vision: 'bg-purple-100 text-purple-700',
    maternity: 'bg-pink-100 text-pink-700',
    emergency: 'bg-orange-100 text-orange-700',
    other: 'bg-gray-100 text-gray-600',
  }
  const label = CLAIM_TYPES.find((t) => t.value === type)?.label ?? type
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${colors[type] ?? 'bg-gray-100 text-gray-600'}`}>
      {label}
    </span>
  )
}

function errMsg(err: unknown) {
  const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
  return d?.errors?.[0]?.message ?? d?.detail ?? 'Something went wrong.'
}

// ── New Claim Modal ────────────────────────────────────────────────────────────

function NewClaimModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    policy_id: '', claim_type: 'hospitalization', incident_date: '',
    description: '', claimed_amount: '',
  })
  const [error, setError] = useState('')

  const policiesQuery = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesApi.list(1),
    enabled: open,
  })
  const policies: Policy[] = policiesQuery.data?.data?.data ?? []

  const mutation = useMutation({
    mutationFn: () => claimsApi.create({
      ...form,
      claimed_amount: parseFloat(form.claimed_amount),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['claims'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
      onClose()
      setForm({ policy_id: '', claim_type: 'hospitalization', incident_date: '', description: '', claimed_amount: '' })
      setError('')
    },
    onError: (err: unknown) => setError(errMsg(err)),
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title="File New Claim">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div>
          <label className="label">Policy <span className="text-red-500">*</span></label>
          <select className="input" value={form.policy_id} onChange={set('policy_id')} required>
            <option value="">Select active policy...</option>
            {policies.filter((p) => p.status === 'active').map((p) => (
              <option key={p.id} value={p.id}>{p.policy_number} — {p.customer_name}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Claim Type <span className="text-red-500">*</span></label>
            <select className="input" value={form.claim_type} onChange={set('claim_type')}>
              {CLAIM_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Incident Date <span className="text-red-500">*</span></label>
            <input className="input" type="date" value={form.incident_date} onChange={set('incident_date')} required />
          </div>
        </div>
        <div>
          <label className="label">Claimed Amount <span className="text-red-500">*</span></label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
            <input className="input pl-7" type="number" min="0.01" step="0.01"
              value={form.claimed_amount} onChange={set('claimed_amount')} placeholder="0.00" required />
          </div>
        </div>
        <div>
          <label className="label">Description <span className="text-red-500">*</span></label>
          <textarea className="input min-h-[80px] resize-none" value={form.description} onChange={set('description')}
            placeholder="Describe the medical event, treatment received, and services claimed..." required minLength={10} />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Filing...' : 'File Claim'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ── Claim Detail Modal ─────────────────────────────────────────────────────────

function ClaimDetailModal({ claimId, onClose }: { claimId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [approvedAmount, setApprovedAmount] = useState('')
  const [rejectReason, setRejectReason] = useState('')
  const [showReject, setShowReject] = useState(false)
  const [error, setError] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['claim', claimId],
    queryFn: () => claimsApi.get(claimId),
  })
  const claim: Claim | undefined = data?.data?.data

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['claims'] })
    queryClient.invalidateQueries({ queryKey: ['claim', claimId] })
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
  }

  const reviewMut = useMutation({
    mutationFn: () => claimsApi.startReview(claimId),
    onSuccess: invalidate,
    onError: (err: unknown) => setError(errMsg(err)),
  })
  const approveMut = useMutation({
    mutationFn: () => claimsApi.approve(claimId, {
      approved_amount: approvedAmount ? parseFloat(approvedAmount) : null,
    }),
    onSuccess: invalidate,
    onError: (err: unknown) => setError(errMsg(err)),
  })
  const rejectMut = useMutation({
    mutationFn: () => claimsApi.reject(claimId, rejectReason),
    onSuccess: () => { invalidate(); onClose() },
    onError: (err: unknown) => setError(errMsg(err)),
  })
  const payMut = useMutation({
    mutationFn: () => claimsApi.pay(claimId),
    onSuccess: invalidate,
    onError: (err: unknown) => setError(errMsg(err)),
  })

  const isWorking = reviewMut.isPending || approveMut.isPending || rejectMut.isPending || payMut.isPending

  return (
    <Modal open={true} onClose={onClose} title="Claim Details" size="md">
      {isLoading && <LoadingSpinner />}
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {claim && (
        <div className="space-y-5">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <p className="font-mono text-sm font-bold text-gray-800">{claim.claim_number}</p>
              <div className="flex items-center gap-2 mt-1">
                {claimTypeBadge(claim.claim_type)}
                <StatusBadge status={claim.status} />
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Claimed</p>
              <p className="text-2xl font-bold text-gray-900">${Number(claim.claimed_amount).toFixed(2)}</p>
              {claim.approved_amount && (
                <p className="text-sm text-green-700 font-medium">
                  Approved: ${Number(claim.approved_amount).toFixed(2)}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            {([
              ['Incident Date', new Date(claim.incident_date).toLocaleDateString()],
              ['Filed', new Date(claim.created_at).toLocaleDateString()],
            ] as [string, string][]).map(([l, v]) => (
              <div key={l} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">{l}</p>
                <p className="font-medium text-gray-900">{v}</p>
              </div>
            ))}
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Description</p>
            <p className="text-sm text-gray-800">{claim.description}</p>
          </div>

          {claim.rejection_reason && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-xs font-medium text-red-600 mb-1">Rejection Reason</p>
              <p className="text-sm text-red-800">{claim.rejection_reason}</p>
            </div>
          )}

          {/* Workflow actions */}
          <div className="border-t border-gray-200 pt-4 space-y-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Actions</p>

            {claim.status === 'submitted' && (
              <div className="flex gap-2">
                <button onClick={() => reviewMut.mutate()} disabled={isWorking}
                  className="btn-secondary flex-1 justify-center gap-2">
                  <Clock className="w-4 h-4" />
                  {reviewMut.isPending ? 'Starting...' : 'Start Review'}
                </button>
                <button onClick={() => setShowReject(!showReject)} disabled={isWorking}
                  className="btn-danger flex-1 justify-center gap-2">
                  <XCircle className="w-4 h-4" /> Reject
                </button>
              </div>
            )}

            {claim.status === 'under_review' && (
              <div className="space-y-3">
                <div>
                  <label className="label">Approved Amount (leave blank to approve full claim)</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                    <input className="input pl-7" type="number" min="0" step="0.01"
                      value={approvedAmount} onChange={(e) => setApprovedAmount(e.target.value)}
                      placeholder={Number(claim.claimed_amount).toFixed(2)} />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => approveMut.mutate()} disabled={isWorking}
                    className="btn-primary flex-1 justify-center gap-2 bg-green-600 hover:bg-green-700">
                    <CheckCircle className="w-4 h-4" />
                    {approveMut.isPending ? 'Approving...' : 'Approve'}
                  </button>
                  <button onClick={() => setShowReject(!showReject)} disabled={isWorking}
                    className="btn-danger flex-1 justify-center gap-2">
                    <XCircle className="w-4 h-4" /> Reject
                  </button>
                </div>
              </div>
            )}

            {claim.status === 'approved' && (
              <button onClick={() => payMut.mutate()} disabled={isWorking}
                className="btn-primary w-full justify-center gap-2 bg-emerald-600 hover:bg-emerald-700">
                <DollarSign className="w-4 h-4" />
                {payMut.isPending ? 'Processing...' : `Pay $${Number(claim.approved_amount ?? claim.claimed_amount).toFixed(2)}`}
              </button>
            )}

            {showReject && (
              <div className="space-y-2 bg-red-50 border border-red-200 rounded-lg p-3">
                <label className="label text-red-700">Rejection Reason <span className="text-red-500">*</span></label>
                <input className="input" value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Reason for rejecting this claim..." />
                <div className="flex gap-2">
                  <button onClick={() => { if (rejectReason.trim()) rejectMut.mutate() }}
                    disabled={isWorking || !rejectReason.trim()} className="btn-danger">
                    Confirm Rejection
                  </button>
                  <button onClick={() => setShowReject(false)} className="btn-secondary">Cancel</button>
                </div>
              </div>
            )}

            {['paid', 'rejected', 'closed', 'withdrawn'].includes(claim.status) && !showReject && (
              <p className="text-sm text-gray-500 italic">No further actions available.</p>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function ClaimsPage() {
  const [showNew, setShowNew] = useState(false)
  const [viewingId, setViewingId] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['claims'],
    queryFn: () => claimsApi.list(1),
  })

  const claims: Claim[] = data?.data?.data ?? []

  const openCount = claims.filter((c) => ['submitted', 'under_review'].includes(c.status)).length
  const approvedCount = claims.filter((c) => c.status === 'approved').length
  const totalClaimed = claims.reduce((s, c) => s + Number(c.claimed_amount), 0)

  return (
    <div className="p-8">
      <PageHeader
        title="Claims"
        subtitle="Medical claim submissions and adjudication"
        action={
          <button className="btn-primary" onClick={() => setShowNew(true)}>
            <Plus className="w-4 h-4" /> File Claim
          </button>
        }
      />

      {claims.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          {[
            { label: 'Open Claims', value: openCount, color: 'text-amber-600' },
            { label: 'Awaiting Payment', value: approvedCount, color: 'text-green-700' },
            { label: 'Total Claimed', value: `$${totalClaimed.toFixed(2)}`, color: 'text-gray-900' },
          ].map(({ label, value, color }) => (
            <div key={label} className="card py-4 text-center">
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
              <p className="text-xs text-gray-500 mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load claims." />}

      {!isLoading && !error && claims.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <AlertCircle className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No claims yet</h3>
          <p className="text-sm text-gray-500 mb-4 max-w-sm">
            File a claim against an active policy to begin the adjudication process.
          </p>
          <button className="btn-primary" onClick={() => setShowNew(true)}>
            <Plus className="w-4 h-4" /> File Claim
          </button>
        </div>
      )}

      {!isLoading && !error && claims.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Claim #', 'Policy', 'Type', 'Incident', 'Claimed', 'Approved', 'Status', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {claims.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{c.claim_number}</td>
                  <td className="px-4 py-3 text-xs text-gray-600">{c.policy_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3">{claimTypeBadge(c.claim_type)}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {new Date(c.incident_date).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900">${Number(c.claimed_amount).toFixed(2)}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.approved_amount ? `$${Number(c.approved_amount).toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                  <td className="px-4 py-3">
                    <button onClick={() => setViewingId(c.id)}
                      className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                      View / Act
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <NewClaimModal open={showNew} onClose={() => setShowNew(false)} />
      {viewingId && <ClaimDetailModal claimId={viewingId} onClose={() => setViewingId(null)} />}
    </div>
  )
}
