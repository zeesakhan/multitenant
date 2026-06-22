import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ShieldAlert, AlertTriangle, CheckCircle, FileText, Plus, Clock,
} from 'lucide-react'
import { amlApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'

function riskBand(score: number): { label: string; color: string } {
  if (score <= 25) return { label: 'LOW', color: 'text-green-700 bg-green-100' }
  if (score <= 50) return { label: 'MEDIUM', color: 'text-amber-700 bg-amber-100' }
  if (score <= 75) return { label: 'HIGH', color: 'text-orange-700 bg-orange-100' }
  return { label: 'CRITICAL', color: 'text-red-700 bg-red-100' }
}

function strStatusBadge(status: string) {
  const styles: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-600',
    pending_approval: 'bg-amber-100 text-amber-700',
    approved: 'bg-blue-100 text-blue-700',
    filed: 'bg-green-100 text-green-700',
    closed: 'bg-gray-100 text-gray-500',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  )
}

interface AmlAlert {
  id: string
  application_id: string
  application_number?: string
  customer_name?: string
  check_type?: string
  status: string
  aml_status?: string
  aml_risk_score?: string | number
  risk_score?: number
  checked_at?: string
  created_at?: string
}

interface StrRecord {
  id: string
  str_reference: string
  application_id: string
  status: string
  nature_of_suspicion: string
  created_at: string
}

function ClearHoldModal({ alert, onClose }: { alert: AmlAlert; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [notes, setNotes] = useState('')

  const clearMut = useMutation({
    mutationFn: () => amlApi.clearHold(alert.application_id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aml-alerts'] })
      toast('AML hold cleared.')
      onClose()
    },
  })

  return (
    <Modal open={true} onClose={onClose} title="Clear AML Hold" level={2}>
      <div className="space-y-4">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 inline mr-1" />
          You are clearing an AML hold. This action is audited and requires justification.
        </div>
        <div>
          <label className="label">Clearance Notes <span className="text-red-500">*</span></label>
          <textarea className="input h-24 resize-none" value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="State the reason for clearing this hold..." />
        </div>
        <div className="flex justify-end gap-3">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary bg-green-600 hover:bg-green-700"
            disabled={!notes.trim() || clearMut.isPending}
            onClick={() => clearMut.mutate()}>
            {clearMut.isPending ? 'Clearing...' : 'Clear Hold'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

function CreateStrModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [form, setForm] = useState({
    application_id: '',
    nature_of_suspicion: '',
    subject_name: '',
    transaction_amount: '',
  })

  const createMut = useMutation({
    mutationFn: () => amlApi.createStr({
      application_id: form.application_id,
      nature_of_suspicion: form.nature_of_suspicion,
      subject_details: { name: form.subject_name },
      transaction_details: { amount: form.transaction_amount },
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['str-records'] })
      toast('STR created.')
      onClose()
    },
  })

  return (
    <Modal open={true} onClose={onClose} title="Create Suspicious Transaction Report" level={2}>
      <div className="space-y-4">
        <div>
          <label className="label">Application ID / Reference</label>
          <input className="input" value={form.application_id}
            onChange={(e) => setForm((f) => ({ ...f, application_id: e.target.value }))}
            placeholder="Application UUID or reference number" />
        </div>
        <div>
          <label className="label">Subject Name</label>
          <input className="input" value={form.subject_name}
            onChange={(e) => setForm((f) => ({ ...f, subject_name: e.target.value }))} />
        </div>
        <div>
          <label className="label">Transaction Amount (AED)</label>
          <input className="input" type="number" value={form.transaction_amount}
            onChange={(e) => setForm((f) => ({ ...f, transaction_amount: e.target.value }))} />
        </div>
        <div>
          <label className="label">Nature of Suspicion <span className="text-red-500">*</span></label>
          <textarea className="input h-28 resize-none" value={form.nature_of_suspicion}
            onChange={(e) => setForm((f) => ({ ...f, nature_of_suspicion: e.target.value }))}
            placeholder="Describe the suspicious activity in detail... (max 2000 characters)"
            maxLength={2000} />
          <p className="text-xs text-gray-400 mt-1">{form.nature_of_suspicion.length}/2000</p>
        </div>
        <div className="flex justify-end gap-3">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary"
            disabled={!form.nature_of_suspicion.trim() || createMut.isPending}
            onClick={() => createMut.mutate()}>
            {createMut.isPending ? 'Creating...' : 'Create STR'}
          </button>
        </div>
      </div>
    </Modal>
  )
}

export default function AmlDashboardPage() {
  const [clearingAlert, setClearingAlert] = useState<AmlAlert | null>(null)
  const [showCreateStr, setShowCreateStr] = useState(false)
  const [approveNotes, setApproveNotes] = useState<Record<string, string>>({})
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['aml-alerts'],
    queryFn: () => amlApi.listAlerts(),
  })

  const { data: strData, isLoading: strLoading } = useQuery({
    queryKey: ['str-records'],
    queryFn: () => amlApi.listStr(),
  })

  const alerts: AmlAlert[] = alertsData?.data?.data ?? []
  const strRecords: StrRecord[] = strData?.data?.data ?? []

  const approveMut = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) => amlApi.approveStr(id, notes),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['str-records'] }); toast('STR approved.') },
  })

  const fileMut = useMutation({
    mutationFn: (id: string) => amlApi.fileStr(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['str-records'] }); toast('STR filed with regulator.') },
  })

  const holdAlerts = alerts.filter((a) => a.aml_status === 'hold' || a.aml_status === 'flagged' || a.status === 'hold' || a.status === 'flagged')
  const strDraft = strRecords.filter((s) => s.status === 'draft').length
  const strPendingApproval = strRecords.filter((s) => s.status === 'pending_approval').length
  const strFiled = strRecords.filter((s) => s.status === 'filed').length

  return (
    <div className="p-8">
      <PageHeader
        title="AML Dashboard"
        subtitle="Anti-Money Laundering monitoring and compliance"
        action={
          <button className="btn-primary" onClick={() => setShowCreateStr(true)}>
            <Plus className="w-4 h-4" /> Create STR
          </button>
        }
      />

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Open AML Alerts', value: holdAlerts.length, icon: ShieldAlert, color: 'bg-red-500' },
          { label: 'STR Draft', value: strDraft, icon: FileText, color: 'bg-gray-500' },
          { label: 'STR Pending Approval', value: strPendingApproval, icon: Clock, color: 'bg-amber-500' },
          { label: 'STR Filed', value: strFiled, icon: CheckCircle, color: 'bg-green-500' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card flex items-center gap-4">
            <div className={`p-3 rounded-xl ${color} flex-shrink-0`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{value}</p>
              <p className="text-sm text-gray-500">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Open AML Alerts */}
      <div className="card mb-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-500" /> Open AML Alerts
        </h2>
        {alertsLoading && <LoadingSpinner />}
        {!alertsLoading && holdAlerts.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-6">No open AML alerts. All clear.</p>
        )}
        {holdAlerts.length > 0 && (
          <div className="rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['Application', 'Customer', 'AML Status', 'Risk Score', 'Date', 'Actions'].map((h) => (
                    <th key={h} className="text-left px-4 py-2.5 font-medium text-gray-600 text-xs">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {holdAlerts.map((a) => {
                  const score = a.aml_risk_score ?? a.risk_score
                  const band = score ? riskBand(Number(score)) : null
                  return (
                    <tr key={a.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-600">{a.application_number ?? a.application_id.slice(0, 8) + '…'}</td>
                      <td className="px-4 py-2.5 text-sm font-medium text-gray-800">{a.customer_name ?? '—'}</td>
                      <td className="px-4 py-2.5">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${
                          (a.aml_status ?? a.status) === 'hold' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                        }`}>{(a.aml_status ?? a.status).replace(/_/g, ' ')}</span>
                      </td>
                      <td className="px-4 py-2.5">
                        {band
                          ? <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${band.color}`}>
                              {score} — {band.label}
                            </span>
                          : '—'}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">
                        {a.checked_at ? new Date(a.checked_at).toLocaleDateString() : a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="px-4 py-2.5">
                        <button
                          onClick={() => setClearingAlert(a)}
                          className="text-xs text-green-600 hover:text-green-700 font-medium"
                        >
                          Clear Hold
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* STR Pipeline */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-400" /> STR Pipeline
          </h2>
        </div>
        {strLoading && <LoadingSpinner />}
        {!strLoading && strRecords.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-6">No STR records.</p>
        )}
        {strRecords.length > 0 && (
          <div className="rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {['STR Reference', 'Application', 'Status', 'Created', 'Actions'].map((h) => (
                    <th key={h} className="text-left px-4 py-2.5 font-medium text-gray-600 text-xs">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {strRecords.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-mono text-xs font-semibold text-gray-800">{s.str_reference}</td>
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-600">{s.application_id?.slice(0, 8)}…</td>
                    <td className="px-4 py-2.5">{strStatusBadge(s.status)}</td>
                    <td className="px-4 py-2.5 text-xs text-gray-500">{new Date(s.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-2.5 flex items-center gap-2">
                      {s.status === 'draft' && (
                        <div className="flex items-center gap-1">
                          <input
                            className="input text-xs h-7 w-32"
                            placeholder="Approval notes..."
                            value={approveNotes[s.id] ?? ''}
                            onChange={(e) => setApproveNotes((n) => ({ ...n, [s.id]: e.target.value }))}
                          />
                          <button
                            onClick={() => approveMut.mutate({ id: s.id, notes: approveNotes[s.id] ?? '' })}
                            disabled={approveMut.isPending}
                            className="text-xs text-blue-600 hover:text-blue-700 font-medium whitespace-nowrap"
                          >
                            Submit for Approval
                          </button>
                        </div>
                      )}
                      {s.status === 'pending_approval' && (
                        <button
                          onClick={() => approveMut.mutate({ id: s.id, notes: 'Approved by senior management' })}
                          disabled={approveMut.isPending}
                          className="text-xs text-green-600 hover:text-green-700 font-medium"
                        >
                          Approve
                        </button>
                      )}
                      {s.status === 'approved' && (
                        <button
                          onClick={() => fileMut.mutate(s.id)}
                          disabled={fileMut.isPending}
                          className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                        >
                          File with Regulator
                        </button>
                      )}
                      {['filed', 'closed'].includes(s.status) && (
                        <span className="text-xs text-gray-400 italic">No further actions</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {clearingAlert && (
        <ClearHoldModal alert={clearingAlert} onClose={() => setClearingAlert(null)} />
      )}
      {showCreateStr && (
        <CreateStrModal onClose={() => setShowCreateStr(false)} />
      )}
    </div>
  )
}
