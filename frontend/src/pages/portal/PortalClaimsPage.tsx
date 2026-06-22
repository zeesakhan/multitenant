import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Plus, X } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'

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

const STATUS_COLORS: Record<string, string> = {
  submitted: 'bg-amber-100 text-amber-700',
  under_review: 'bg-blue-100 text-blue-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  paid: 'bg-emerald-100 text-emerald-700',
  closed: 'bg-gray-100 text-gray-500',
  withdrawn: 'bg-gray-100 text-gray-400',
}

function fmt(n: string | number) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export default function PortalClaimsPage() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [filter, setFilter] = useState('all')
  const [claimType, setClaimType] = useState('hospitalization')
  const [incidentDate, setIncidentDate] = useState('')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [formError, setFormError] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['portal-claims'],
    queryFn: portalCustomerApi.getClaims,
    retry: false,
  })

  const membersQ = useQuery({ queryKey: ['portal-members'], queryFn: portalCustomerApi.getMembers, retry: false })
  const members: Record<string, unknown>[] = membersQ.data?.data?.data ?? []

  const [selectedMember, setSelectedMember] = useState('')

  const mutation = useMutation({
    mutationFn: portalCustomerApi.fileClaim,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal-claims'] })
      setShowModal(false)
      resetForm()
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setFormError(msg ?? 'Failed to submit claim.')
    },
  })

  function resetForm() {
    setClaimType('hospitalization'); setIncidentDate(''); setDescription('')
    setAmount(''); setSelectedMember(''); setFormError('')
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setFormError('')
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
      setFormError('Enter a valid claim amount.')
      return
    }
    mutation.mutate({
      claim_type: claimType,
      incident_date: incidentDate,
      description,
      claimed_amount: Number(amount),
      member_id: selectedMember || undefined,
    })
  }

  const allClaims: Record<string, unknown>[] = data?.data?.data ?? []
  const filtered = filter === 'all' ? allClaims : allClaims.filter((c) => c.status === filter)

  const tabs = ['all', 'submitted', 'under_review', 'approved', 'paid', 'rejected']

  return (
    <div className="p-8">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Claims</h1>
          <p className="text-gray-500 text-sm mt-1">{allClaims.length} claim{allClaims.length !== 1 ? 's' : ''} on record.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> File a Claim
        </button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-colors ${
              filter === t ? 'bg-emerald-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {t === 'all' ? `All (${allClaims.length})` : t.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Claims list */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <p className="p-6 text-sm text-gray-400">Loading claims…</p>
        ) : filtered.length === 0 ? (
          <div className="p-10 text-center">
            <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No claims {filter !== 'all' ? `with status "${filter.replace(/_/g, ' ')}"` : 'filed yet'}.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Claim #', 'Type', 'Incident Date', 'Claimed', 'Approved', 'Status', 'Filed'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((c) => (
                <tr key={String(c.id)} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{String(c.claim_number)}</td>
                  <td className="px-4 py-3 capitalize text-gray-600">{String(c.claim_type ?? '').replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {c.incident_date ? new Date(String(c.incident_date)).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3 font-semibold text-gray-900">AED {fmt(String(c.claimed_amount))}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.approved_amount ? `AED AED {fmt(String(c.approved_amount))}` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_COLORS[String(c.status)] ?? 'bg-gray-100 text-gray-500'}`}>
                      {String(c.status).replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {c.created_at ? new Date(String(c.created_at)).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* File Claim Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">File a New Claim</h2>
              <button onClick={() => { setShowModal(false); resetForm() }} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{formError}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Claim Type</label>
                <select className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={claimType} onChange={(e) => setClaimType(e.target.value)}>
                  {CLAIM_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              {members.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Member (optional)</label>
                  <select className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    value={selectedMember} onChange={(e) => setSelectedMember(e.target.value)}>
                    <option value="">All members</option>
                    {members.map((m) => (
                      <option key={String(m.id)} value={String(m.id)}>
                        {String(m.first_name)} {String(m.last_name)} ({String(m.relationship)})
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Incident Date</label>
                <input type="date" required
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={incidentDate} onChange={(e) => setIncidentDate(e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Claimed Amount ($)</label>
                <input type="number" min="0.01" step="0.01" required
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea required rows={3}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
                  value={description} onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the medical event or treatment…" />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setShowModal(false); resetForm() }}
                  className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                  Cancel
                </button>
                <button type="submit" disabled={mutation.isPending}
                  className="flex-1 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
                  {mutation.isPending ? 'Submitting…' : 'Submit Claim'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
