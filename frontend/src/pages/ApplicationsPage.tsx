import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FileText, CheckCircle, XCircle, Send, ShieldCheck, Trash2, BadgeCheck, Users } from 'lucide-react'
import { applicationsApi, productsApi, plansApi, membersApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { Product, Plan, ApplicationItem, Member } from '../types'

const RELATIONSHIPS = ['self', 'spouse', 'child', 'parent', 'sibling', 'dependent']
const GENDERS = [
  { value: 'M', label: 'Male' },
  { value: 'F', label: 'Female' },
  { value: 'O', label: 'Other' },
  { value: 'U', label: 'Undisclosed' },
]

function calcAge(dob: string): number {
  const today = new Date()
  const birth = new Date(dob)
  let age = today.getFullYear() - birth.getFullYear()
  if (today < new Date(today.getFullYear(), birth.getMonth(), birth.getDate())) age--
  return age
}

function relBadge(rel: string) {
  const colors: Record<string, string> = {
    self: 'bg-blue-100 text-blue-700',
    spouse: 'bg-pink-100 text-pink-700',
    child: 'bg-green-100 text-green-700',
    parent: 'bg-orange-100 text-orange-700',
    sibling: 'bg-purple-100 text-purple-700',
    dependent: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${colors[rel] ?? 'bg-gray-100 text-gray-600'}`}>
      {rel}
    </span>
  )
}

function errMsg(err: unknown) {
  const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
  return d?.errors?.[0]?.message ?? d?.detail ?? 'Something went wrong.'
}

interface AppRow {
  id: string
  application_number: string
  customer_name: string
  customer_email: string
  status: string
  total_premium: string
  member_count: number
  plan_id?: string | null
  product_id?: string | null
  created_at: string
}

// ── New Application Modal ──────────────────────────────────────────────────────

function NewApplicationModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    product_id: '', plan_id: '', customer_name: '', customer_email: '', member_count: 1,
  })
  const [error, setError] = useState('')

  const productsQuery = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.list(1),
    enabled: open,
  })
  const plansQuery = useQuery({
    queryKey: ['plans', form.product_id],
    queryFn: () => plansApi.list(form.product_id),
    enabled: !!form.product_id,
  })

  const products: Product[] = productsQuery.data?.data?.data ?? productsQuery.data?.data?.items ?? []
  const plans: Plan[] = plansQuery.data?.data?.data ?? plansQuery.data?.data?.items ?? []
  const selectedPlan = plans.find((p) => p.id === form.plan_id)

  const mutation = useMutation({
    mutationFn: () => applicationsApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      onClose()
      setForm({ product_id: '', plan_id: '', customer_name: '', customer_email: '', member_count: 1 })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const handleProductChange = (e: React.ChangeEvent<HTMLSelectElement>) =>
    setForm((f) => ({ ...f, product_id: e.target.value, plan_id: '' }))

  return (
    <Modal open={open} onClose={onClose} title="New Application">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div>
          <label className="label">Product</label>
          {productsQuery.isLoading
            ? <p className="text-sm text-gray-400">Loading...</p>
            : (
              <select className="input" value={form.product_id} onChange={handleProductChange}>
                <option value="">Select a product (optional)...</option>
                {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            )}
        </div>
        {form.product_id && (
          <div>
            <label className="label">Plan</label>
            {plansQuery.isLoading
              ? <p className="text-sm text-gray-400">Loading plans...</p>
              : plans.length === 0
                ? <p className="text-sm text-amber-600">No active plans for this product.</p>
                : (
                  <select className="input" value={form.plan_id}
                    onChange={(e) => setForm((f) => ({ ...f, plan_id: e.target.value }))}>
                    <option value="">Select a plan...</option>
                    {plans.filter((p) => p.is_active).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — ${Number(p.base_premium).toFixed(2)}/mo
                      </option>
                    ))}
                  </select>
                )}
          </div>
        )}
        {selectedPlan && (
          <div className="flex items-center justify-between px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg">
            <span className="text-sm text-emerald-700">Plan Premium</span>
            <span className="text-lg font-bold text-emerald-700">${Number(selectedPlan.base_premium).toFixed(2)}/mo</span>
          </div>
        )}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Customer Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.customer_name}
              onChange={(e) => setForm((f) => ({ ...f, customer_name: e.target.value }))}
              placeholder="Jane Smith" required />
          </div>
          <div>
            <label className="label">Customer Email <span className="text-red-500">*</span></label>
            <input className="input" type="email" value={form.customer_email}
              onChange={(e) => setForm((f) => ({ ...f, customer_email: e.target.value }))}
              placeholder="jane@example.com" required />
          </div>
        </div>
        <div>
          <label className="label">Number of Members</label>
          <input className="input" type="number" min={1} max={20} value={form.member_count}
            onChange={(e) => setForm((f) => ({ ...f, member_count: Number(e.target.value) }))} />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create Application'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ── Add Item Modal ─────────────────────────────────────────────────────────────

function AddItemModal({ open, onClose, appId, planId, productId }: {
  open: boolean; onClose: () => void; appId: string; planId: string; productId: string
}) {
  const queryClient = useQueryClient()
  const [coverageId, setCoverageId] = useState('')
  const [premium, setPremium] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')

  const plansQuery = useQuery({
    queryKey: ['plans', productId],
    queryFn: () => plansApi.list(productId),
    enabled: open && !!productId,
  })
  const plans: Plan[] = plansQuery.data?.data?.data ?? plansQuery.data?.data?.items ?? []
  const plan = plans.find((p) => p.id === planId)
  const coverages = plan?.coverages ?? []

  const mutation = useMutation({
    mutationFn: () => applicationsApi.addItem(appId, {
      coverage_id: coverageId,
      premium: parseFloat(premium),
      notes: notes || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
      onClose()
      setCoverageId(''); setPremium(''); setNotes(''); setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  return (
    <Modal open={open} onClose={onClose} title="Add Coverage Item" level={2}>
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      {coverages.length === 0
        ? <p className="text-sm text-gray-500">No coverages configured for this plan. Add coverages in Products → Plans first.</p>
        : (
          <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
            <div>
              <label className="label">Coverage <span className="text-red-500">*</span></label>
              <select className="input" value={coverageId}
                onChange={(e) => setCoverageId(e.target.value)} required>
                <option value="">Select coverage...</option>
                {coverages.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.coverage_type})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Premium <span className="text-red-500">*</span></label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
                <input className="input pl-7" type="number" min="0.01" step="0.01"
                  value={premium} onChange={(e) => setPremium(e.target.value)} placeholder="0.00" required />
              </div>
            </div>
            <div>
              <label className="label">Notes</label>
              <input className="input" value={notes} onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional notes..." />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
              <button type="submit" className="btn-primary" disabled={mutation.isPending}>
                {mutation.isPending ? 'Adding...' : 'Add Item'}
              </button>
            </div>
          </form>
        )}
    </Modal>
  )
}

// ── Add Member Modal ───────────────────────────────────────────────────────────

function AddMemberModal({ open, onClose, appId }: { open: boolean; onClose: () => void; appId: string }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    first_name: '', last_name: '', date_of_birth: '',
    relationship: 'self', gender: 'M', email: '', phone: '',
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => membersApi.add(appId, {
      ...form,
      email: form.email || null,
      phone: form.phone || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
      onClose()
      setForm({ first_name: '', last_name: '', date_of_birth: '', relationship: 'self', gender: 'M', email: '', phone: '' })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title="Add Member" level={2}>
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.first_name} onChange={set('first_name')} placeholder="Jane" required />
          </div>
          <div>
            <label className="label">Last Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.last_name} onChange={set('last_name')} placeholder="Smith" required />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Date of Birth <span className="text-red-500">*</span></label>
            <input className="input" type="date" value={form.date_of_birth} onChange={set('date_of_birth')} required />
          </div>
          <div>
            <label className="label">Relationship <span className="text-red-500">*</span></label>
            <select className="input" value={form.relationship} onChange={set('relationship')}>
              {RELATIONSHIPS.map((r) => (
                <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Gender <span className="text-red-500">*</span></label>
            <select className="input" value={form.gender} onChange={set('gender')}>
              {GENDERS.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Phone</label>
            <input className="input" value={form.phone} onChange={set('phone')} placeholder="+1 555 000 0000" />
          </div>
        </div>
        <div>
          <label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={set('email')} placeholder="member@example.com" />
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Adding...' : 'Add Member'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ── Application Detail Modal ───────────────────────────────────────────────────

function ApplicationDetailModal({ appId, onClose }: { appId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [rejectReason, setRejectReason] = useState('')
  const [showReject, setShowReject] = useState(false)
  const [showAddItem, setShowAddItem] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)
  const [error, setError] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['application', appId],
    queryFn: () => applicationsApi.get(appId),
  })

  const app = data?.data?.data as (AppRow & { items?: ApplicationItem[]; members?: Member[]; additional_info?: Record<string, unknown> }) | undefined

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['applications'] })
    queryClient.invalidateQueries({ queryKey: ['application', appId] })
  }

  const submitMut = useMutation({
    mutationFn: () => applicationsApi.submit(appId),
    onSuccess: () => { invalidate() },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })
  const approveMut = useMutation({
    mutationFn: () => applicationsApi.approve(appId),
    onSuccess: () => { invalidate() },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })
  const rejectMut = useMutation({
    mutationFn: () => applicationsApi.reject(appId, rejectReason),
    onSuccess: () => { invalidate(); onClose() },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })
  const removeMut = useMutation({
    mutationFn: (itemId: string) => applicationsApi.removeItem(appId, itemId),
    onSuccess: () => { invalidate() },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })
  const removeMemberMut = useMutation({
    mutationFn: (memberId: string) => membersApi.remove(appId, memberId),
    onSuccess: () => { invalidate() },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })
  const issueMut = useMutation({
    mutationFn: () => applicationsApi.issue(appId),
    onSuccess: () => {
      invalidate()
      queryClient.invalidateQueries({ queryKey: ['policies'] })
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const isWorking = submitMut.isPending || approveMut.isPending || rejectMut.isPending || issueMut.isPending

  return (
    <>
      <Modal open={true} onClose={onClose} title="Application Details" size="lg">
        {isLoading && <LoadingSpinner />}
        {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}

        {app && (
          <div className="space-y-5">
            {/* Summary grid */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              {([
                ['Ref #', app.application_number],
                ['Customer', app.customer_name],
                ['Email', app.customer_email],
                ['Members', String(app.member_count)],
                ['Premium', `$${Number(app.total_premium).toFixed(2)}/mo`],
                ['Status', null],
              ] as [string, string | null][]).map(([label, value]) => (
                <div key={label} className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">{label}</p>
                  {value !== null
                    ? <p className="font-medium text-gray-900">{value}</p>
                    : <StatusBadge status={app.status} />}
                </div>
              ))}
            </div>

            {/* Issued policy banner */}
            {app.status === 'issued' && (
              <div className="flex items-center gap-3 px-4 py-3 bg-green-50 border border-green-200 rounded-xl">
                <BadgeCheck className="w-5 h-5 text-green-600 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-green-800">Policy Issued</p>
                  <p className="text-xs text-green-600">Go to Policies to view the full policy details.</p>
                </div>
              </div>
            )}

            {/* Members */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                  <Users className="w-4 h-4 text-gray-400" /> Members
                  <span className="text-xs font-normal text-gray-400">({app.members?.length ?? 0} of {app.member_count})</span>
                </p>
                {app.status === 'draft' && (
                  <button onClick={() => setShowAddMember(true)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Add Member
                  </button>
                )}
              </div>

              {(!app.members || app.members.length === 0)
                ? (
                  <div className="py-4 text-center border border-dashed border-gray-200 rounded-lg">
                    <p className="text-xs text-gray-400">No members added yet</p>
                  </div>
                )
                : (
                  <div className="rounded-lg border border-gray-200 overflow-hidden">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50">
                        <tr>
                          {['Name', 'DOB / Age', 'Relationship', 'Gender', ''].map((h) => (
                            <th key={h} className="text-left px-3 py-2 font-medium text-gray-600">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {app.members.map((m) => (
                          <tr key={m.id} className="hover:bg-gray-50">
                            <td className="px-3 py-2 font-medium text-gray-900">
                              {m.first_name} {m.last_name}
                            </td>
                            <td className="px-3 py-2 text-gray-500">
                              {new Date(m.date_of_birth).toLocaleDateString()}
                              <span className="ml-1 text-gray-400">({calcAge(m.date_of_birth)}y)</span>
                            </td>
                            <td className="px-3 py-2">{relBadge(m.relationship)}</td>
                            <td className="px-3 py-2 text-gray-500">
                              {GENDERS.find(g => g.value === m.gender)?.label ?? m.gender}
                            </td>
                            <td className="px-3 py-2">
                              {app.status === 'draft' && (
                                <button onClick={() => removeMemberMut.mutate(m.id)}
                                  className="text-red-400 hover:text-red-600">
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>

            {/* Coverage Items */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">Coverage Items</p>
                {app.status === 'draft' && app.plan_id && app.product_id && (
                  <button onClick={() => setShowAddItem(true)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Add Item
                  </button>
                )}
                {app.status === 'draft' && !app.plan_id && (
                  <span className="text-xs text-gray-400 italic">Select a plan to add items</span>
                )}
              </div>

              {(!app.items || app.items.length === 0)
                ? (
                  <div className="py-4 text-center border border-dashed border-gray-200 rounded-lg">
                    <p className="text-xs text-gray-400">No coverage items yet</p>
                  </div>
                )
                : (
                  <div className="rounded-lg border border-gray-200 overflow-hidden">
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50">
                        <tr>
                          {['Coverage', 'Type', 'Premium', 'Status', ''].map((h) => (
                            <th key={h} className="text-left px-3 py-2 font-medium text-gray-600">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {app.items.map((item) => (
                          <tr key={item.id} className="hover:bg-gray-50">
                            <td className="px-3 py-2 font-medium text-gray-900">
                              {item.coverage?.name ?? item.coverage_id.slice(0, 8)}
                            </td>
                            <td className="px-3 py-2 text-gray-500 capitalize">
                              {item.coverage?.coverage_type?.replace(/_/g, ' ') ?? '—'}
                            </td>
                            <td className="px-3 py-2 text-gray-700">${Number(item.premium).toFixed(2)}</td>
                            <td className="px-3 py-2">
                              <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${
                                item.status === 'approved' ? 'bg-green-100 text-green-700'
                                  : item.status === 'rejected' ? 'bg-red-100 text-red-600'
                                  : 'bg-gray-100 text-gray-600'
                              }`}>{item.status}</span>
                            </td>
                            <td className="px-3 py-2">
                              {app.status === 'draft' && (
                                <button onClick={() => removeMut.mutate(item.id)}
                                  className="text-red-400 hover:text-red-600">
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>

            {/* Workflow Actions */}
            <div className="border-t border-gray-200 pt-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Actions</p>

              {app.status === 'draft' && (
                <button onClick={() => submitMut.mutate()} disabled={isWorking}
                  className="btn-primary w-full justify-center gap-2">
                  <Send className="w-4 h-4" />
                  {submitMut.isPending ? 'Submitting...' : 'Submit for Review'}
                </button>
              )}

              {app.status === 'submitted' && (
                <div className="flex gap-2">
                  <button onClick={() => approveMut.mutate()} disabled={isWorking}
                    className="btn-primary flex-1 justify-center gap-2 bg-green-600 hover:bg-green-700">
                    <CheckCircle className="w-4 h-4" />
                    {approveMut.isPending ? 'Approving...' : 'Approve'}
                  </button>
                  <button onClick={() => setShowReject(true)} disabled={isWorking}
                    className="btn-danger flex-1 justify-center gap-2">
                    <XCircle className="w-4 h-4" /> Reject
                  </button>
                </div>
              )}

              {app.status === 'approved' && (
                <div className="space-y-2">
                  <button onClick={() => issueMut.mutate()} disabled={isWorking}
                    className="btn-primary w-full justify-center gap-2 bg-violet-600 hover:bg-violet-700">
                    <ShieldCheck className="w-4 h-4" />
                    {issueMut.isPending ? 'Issuing...' : 'Issue Policy'}
                  </button>
                  <p className="text-xs text-gray-400 text-center">
                    Generates a policy number and activates coverage.
                  </p>
                </div>
              )}

              {showReject && (
                <div className="mt-3 space-y-2">
                  <label className="label">Rejection Reason <span className="text-red-500">*</span></label>
                  <input className="input" value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Reason for rejection..." />
                  <div className="flex gap-2">
                    <button onClick={() => { if (rejectReason.trim()) rejectMut.mutate() }}
                      disabled={isWorking || !rejectReason.trim()} className="btn-danger">
                      Confirm Rejection
                    </button>
                    <button onClick={() => setShowReject(false)} className="btn-secondary">Cancel</button>
                  </div>
                </div>
              )}

              {['issued', 'rejected', 'cancelled'].includes(app.status) && !showReject && (
                <p className="text-sm text-gray-500 italic">
                  No further actions available for a <strong>{app.status}</strong> application.
                </p>
              )}

            </div>
          </div>
        )}
      </Modal>

      {app?.plan_id && app?.product_id && (
        <AddItemModal
          open={showAddItem}
          onClose={() => setShowAddItem(false)}
          appId={appId}
          planId={app.plan_id}
          productId={app.product_id}
        />
      )}

      <AddMemberModal
        open={showAddMember}
        onClose={() => setShowAddMember(false)}
        appId={appId}
      />
    </>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function ApplicationsPage() {
  const [showNew, setShowNew] = useState(false)
  const [viewingId, setViewingId] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: () => applicationsApi.list(1),
  })

  const applications: AppRow[] = data?.data?.data ?? data?.data?.items ?? []

  return (
    <div className="p-8">
      <PageHeader
        title="Applications"
        subtitle="Insurance applications and enrollment workflow"
        action={
          <button className="btn-primary" onClick={() => setShowNew(true)}>
            <Plus className="w-4 h-4" /> New Application
          </button>
        }
      />

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load applications." />}

      {!isLoading && !error && applications.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <FileText className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No applications yet</h3>
          <p className="text-sm text-gray-500 mb-4 max-w-sm">
            Create an application directly or convert a quote.
          </p>
          <button className="btn-primary" onClick={() => setShowNew(true)}>
            <Plus className="w-4 h-4" /> New Application
          </button>
        </div>
      )}

      {!isLoading && !error && applications.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Ref #', 'Customer', 'Email', 'Members', 'Premium', 'Status', 'Created', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {applications.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{a.application_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{a.customer_name}</td>
                  <td className="px-4 py-3 text-gray-600">{a.customer_email}</td>
                  <td className="px-4 py-3 text-center text-gray-600">{a.member_count}</td>
                  <td className="px-4 py-3 text-gray-600">${Number(a.total_premium).toFixed(2)}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {a.created_at ? new Date(a.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => setViewingId(a.id)}
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

      <NewApplicationModal open={showNew} onClose={() => setShowNew(false)} />
      {viewingId && <ApplicationDetailModal appId={viewingId} onClose={() => setViewingId(null)} />}
    </div>
  )
}
