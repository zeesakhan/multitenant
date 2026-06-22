import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Globe, CheckCircle, AlertTriangle, RefreshCw, Shield } from 'lucide-react'
import { govtChecksApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'

interface GovtCheckRecord {
  id: string
  application_id: string
  member_id?: string
  check_type: string
  status: string
  triggered_at: string
  resolved_at?: string
  override_justification?: string
}

const CHECK_TYPE_LABELS: Record<string, string> = {
  icp: 'ICP (Emirates ID)',
  dha: 'DHA Health',
  ofac: 'OFAC Sanctions',
  un_sanctions: 'UN Sanctions',
  uae_cabinet_74: 'UAE Cabinet 74',
  eu_sanctions: 'EU Sanctions',
  hmt_sanctions: 'HMT Sanctions',
}

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    verified: 'bg-green-100 text-green-700',
    mismatch: 'bg-red-100 text-red-700',
    not_found: 'bg-orange-100 text-orange-700',
    failed: 'bg-red-100 text-red-600',
    overridden: 'bg-purple-100 text-purple-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  )
}

function OverrideModal({
  record,
  onClose,
}: { record: GovtCheckRecord; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [justification, setJustification] = useState('')

  const overrideMut = useMutation({
    mutationFn: () => govtChecksApi.override(record.id, justification),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['govt-checks'] })
      toast('Check overridden and audit record created.')
      onClose()
    },
  })

  return (
    <Modal open={true} onClose={onClose} title="Override Government Check" level={2}>
      <div className="space-y-4">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 inline mr-1" />
          Overriding a failed check creates a permanent audit record. This action requires justification and cannot be undone.
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Check Type</p>
            <p className="font-medium">{CHECK_TYPE_LABELS[record.check_type] ?? record.check_type}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Current Status</p>
            <div className="mt-0.5">{statusBadge(record.status)}</div>
          </div>
        </div>
        <div>
          <label className="label">Override Justification <span className="text-red-500">*</span></label>
          <textarea className="input h-28 resize-none" value={justification}
            onChange={(e) => setJustification(e.target.value)}
            placeholder="Provide a detailed justification for overriding this check..." />
        </div>
        <div className="flex justify-end gap-3">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary bg-amber-600 hover:bg-amber-700"
            disabled={!justification.trim() || overrideMut.isPending}
            onClick={() => overrideMut.mutate()}>
            {overrideMut.isPending ? 'Overriding...' : 'Override Check'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

const STATUS_OPTIONS = [
  { label: 'All Status', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Verified', value: 'verified' },
  { label: 'Failed', value: 'failed' },
  { label: 'Mismatch', value: 'mismatch' },
  { label: 'Not Found', value: 'not_found' },
  { label: 'Overridden', value: 'overridden' },
]

const TYPE_OPTIONS = [
  { label: 'All Types', value: '' },
  { label: 'ICP (Emirates ID)', value: 'icp' },
  { label: 'OFAC', value: 'ofac' },
  { label: 'UN Sanctions', value: 'un_sanctions' },
  { label: 'UAE Cabinet 74', value: 'uae_cabinet_74' },
  { label: 'DHA', value: 'dha' },
]

export default function GovtChecksPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [overridingRecord, setOverridingRecord] = useState<GovtCheckRecord | null>(null)
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['govt-checks', statusFilter, typeFilter],
    queryFn: () => govtChecksApi.list({
      status_filter: statusFilter || undefined,
      check_type: typeFilter || undefined,
    }),
  })

  const records: GovtCheckRecord[] = data?.data?.data ?? []

  const bulkRetryMut = useMutation({
    mutationFn: () => govtChecksApi.bulkRetry(Array.from(selectedIds)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['govt-checks'] })
      toast(`Retrying ${selectedIds.size} checks.`)
      setSelectedIds(new Set())
    },
  })

  function toggleSelect(id: string) {
    setSelectedIds((s) => {
      const next = new Set(s)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (selectedIds.size === records.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(records.map((r) => r.id)))
    }
  }

  const pendingCount = records.filter((r) => r.status === 'pending').length
  const failedCount = records.filter((r) => ['failed', 'mismatch', 'not_found'].includes(r.status)).length
  const verifiedCount = records.filter((r) => r.status === 'verified').length
  const overriddenCount = records.filter((r) => r.status === 'overridden').length

  return (
    <div className="p-8">
      <PageHeader
        title="Government Checks"
        subtitle="ICP, sanctions and regulatory verification records"
      />

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Pending', value: pendingCount, color: 'bg-amber-500' },
          { label: 'Failed / Mismatch', value: failedCount, color: 'bg-red-500' },
          { label: 'Verified', value: verifiedCount, color: 'bg-green-500' },
          { label: 'Overridden', value: overriddenCount, color: 'bg-purple-500' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`p-3 rounded-xl ${color} flex-shrink-0`}>
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-sm text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filter bar + bulk actions */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select className="input w-44 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {STATUS_OPTIONS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        <select className="input w-44 text-sm" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          {TYPE_OPTIONS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        {selectedIds.size > 0 && (
          <button
            onClick={() => bulkRetryMut.mutate()}
            disabled={bulkRetryMut.isPending}
            className="btn-primary text-sm flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {bulkRetryMut.isPending ? 'Retrying...' : `Retry ${selectedIds.size} Selected`}
          </button>
        )}
        {(statusFilter || typeFilter) && (
          <button className="text-sm text-gray-500 hover:text-gray-700"
            onClick={() => { setStatusFilter(''); setTypeFilter('') }}>
            Clear filters
          </button>
        )}
      </div>

      {isLoading && <LoadingSpinner />}

      {!isLoading && records.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <Globe className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No records found</h3>
          <p className="text-sm text-gray-500">Government verification records will appear here as applications are submitted.</p>
        </div>
      )}

      {!isLoading && records.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3">
                  <input type="checkbox" className="rounded" checked={selectedIds.size === records.length && records.length > 0}
                    onChange={toggleAll} />
                </th>
                {['Application', 'Check Type', 'Status', 'Triggered', 'Resolved', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600 text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <input type="checkbox" className="rounded" checked={selectedIds.has(r.id)}
                      onChange={() => toggleSelect(r.id)} />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{r.application_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-700">
                    {CHECK_TYPE_LABELS[r.check_type] ?? r.check_type}
                  </td>
                  <td className="px-4 py-3">{statusBadge(r.status)}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {new Date(r.triggered_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {r.resolved_at ? new Date(r.resolved_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3 flex items-center gap-2">
                    {['failed', 'mismatch', 'not_found'].includes(r.status) && (
                      <>
                        <button
                          onClick={() => bulkRetryMut.mutate()}
                          className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                        >
                          <RefreshCw className="w-3 h-3" /> Retry
                        </button>
                        <button
                          onClick={() => setOverridingRecord(r)}
                          className="text-xs text-amber-600 hover:text-amber-700 font-medium flex items-center gap-1"
                        >
                          Override
                        </button>
                      </>
                    )}
                    {r.status === 'pending' && (
                      <button
                        onClick={() => bulkRetryMut.mutate()}
                        className="text-xs text-gray-500 hover:text-gray-700 font-medium flex items-center gap-1"
                      >
                        <RefreshCw className="w-3 h-3" /> Retry
                      </button>
                    )}
                    {r.status === 'verified' && (
                      <span className="flex items-center gap-1 text-xs text-green-600">
                        <CheckCircle className="w-3 h-3" /> Verified
                      </span>
                    )}
                    {r.status === 'overridden' && (
                      <span className="text-xs text-gray-400 italic" title={r.override_justification}>
                        Overridden
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {overridingRecord && (
        <OverrideModal record={overridingRecord} onClose={() => setOverridingRecord(null)} />
      )}
    </div>
  )
}
