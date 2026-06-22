import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, FileText, CheckCircle, XCircle, Send, ShieldCheck, Trash2,
  BadgeCheck, Users, MessageSquare, DollarSign, Download, RefreshCw,
} from 'lucide-react'
import { applicationsApi, productsApi, plansApi, membersApi, documentsApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'
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

function AmlBadge({ status }: { status?: string }) {
  if (!status || status === 'clear') return null
  const styles: Record<string, string> = {
    flagged: 'bg-orange-100 text-orange-700 border border-orange-200',
    hold: 'bg-red-100 text-red-700 border border-red-200',
    cleared: 'bg-green-100 text-green-700 border border-green-200',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      AML {status}
    </span>
  )
}

function GovtBadge({ status }: { status?: string }) {
  if (!status) return null
  const styles: Record<string, string> = {
    pending: 'bg-amber-100 text-amber-700',
    verified: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
    overridden: 'bg-purple-100 text-purple-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      Govt {status}
    </span>
  )
}

interface AppRow {
  id: string
  application_number: string
  customer_name: string
  customer_email: string
  status: string
  aml_status?: string
  govt_check_status?: string
  total_premium: string
  member_count: number
  plan_id?: string | null
  product_id?: string | null
  created_at: string
}

// ── New Application Modal ──────────────────────────────────────────────────────

function NewApplicationModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
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
      toast('Application created.')
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
                        {p.name} — AED {Number(p.base_premium).toFixed(2)}/yr
                      </option>
                    ))}
                  </select>
                )}
          </div>
        )}
        {selectedPlan && (
          <div className="flex items-center justify-between px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg">
            <span className="text-sm text-emerald-700">Plan Premium</span>
            <span className="text-lg font-bold text-emerald-700">AED {Number(selectedPlan.base_premium).toFixed(2)}/yr</span>
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
  const { toast } = useToast()
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
      toast('Coverage item added.')
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
              <label className="label">Premium (AED) <span className="text-red-500">*</span></label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">AED</span>
                <input className="input pl-12" type="number" min="0.01" step="0.01"
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
  const { toast } = useToast()
  const [form, setForm] = useState({
    first_name: '', last_name: '', date_of_birth: '',
    relationship: 'self', gender: 'M', email: '', phone: '',
    emirates_id: '', passport_number: '', nationality: '',
    visa_type: '', marital_status: '', occupation: '',
    height_cm: '', weight_kg: '',
  })
  const [error, setError] = useState('')
  const [eidError, setEidError] = useState('')

  const EID_PATTERN = /^784-\d{4}-\d{7}-\d$/

  const mutation = useMutation({
    mutationFn: () => membersApi.add(appId, {
      ...form,
      email: form.email || null,
      phone: form.phone || null,
      emirates_id: form.emirates_id || null,
      passport_number: form.passport_number || null,
      height_cm: form.height_cm ? Number(form.height_cm) : null,
      weight_kg: form.weight_kg ? Number(form.weight_kg) : null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['application', appId] })
      toast('Member added.')
      onClose()
      setForm({
        first_name: '', last_name: '', date_of_birth: '', relationship: 'self', gender: 'M',
        email: '', phone: '', emirates_id: '', passport_number: '', nationality: '',
        visa_type: '', marital_status: '', occupation: '', height_cm: '', weight_kg: '',
      })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  function validateEid(val: string) {
    if (val && !EID_PATTERN.test(val)) {
      setEidError('Format: 784-YYYY-NNNNNNN-C')
    } else {
      setEidError('')
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add Member">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => {
        e.preventDefault()
        setError('')
        if (form.emirates_id && !EID_PATTERN.test(form.emirates_id)) {
          setEidError('Format: 784-YYYY-NNNNNNN-C')
          return
        }
        mutation.mutate()
      }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.first_name}
              onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))} required />
          </div>
          <div>
            <label className="label">Last Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.last_name}
              onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))} required />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Date of Birth <span className="text-red-500">*</span></label>
            <input className="input" type="date" value={form.date_of_birth}
              onChange={(e) => setForm((f) => ({ ...f, date_of_birth: e.target.value }))} required />
          </div>
          <div>
            <label className="label">Gender</label>
            <select className="input" value={form.gender}
              onChange={(e) => setForm((f) => ({ ...f, gender: e.target.value }))}>
              {GENDERS.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Relationship</label>
            <select className="input" value={form.relationship}
              onChange={(e) => setForm((f) => ({ ...f, relationship: e.target.value }))}>
              {RELATIONSHIPS.map((r) => <option key={r} value={r} className="capitalize">{r}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Marital Status</label>
            <select className="input" value={form.marital_status}
              onChange={(e) => setForm((f) => ({ ...f, marital_status: e.target.value }))}>
              <option value="">Select...</option>
              {['single', 'married', 'divorced', 'widowed'].map((s) => (
                <option key={s} value={s} className="capitalize">{s}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Emirates ID</label>
            <input className="input" value={form.emirates_id}
              placeholder="784-YYYY-NNNNNNN-C"
              onChange={(e) => { setForm((f) => ({ ...f, emirates_id: e.target.value })); validateEid(e.target.value) }}
            />
            {eidError && <p className="text-xs text-red-500 mt-1">{eidError}</p>}
          </div>
          <div>
            <label className="label">Passport Number</label>
            <input className="input" value={form.passport_number}
              onChange={(e) => setForm((f) => ({ ...f, passport_number: e.target.value }))} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Nationality</label>
            <input className="input" value={form.nationality}
              onChange={(e) => setForm((f) => ({ ...f, nationality: e.target.value }))} />
          </div>
          <div>
            <label className="label">Visa Type</label>
            <select className="input" value={form.visa_type}
              onChange={(e) => setForm((f) => ({ ...f, visa_type: e.target.value }))}>
              <option value="">Select...</option>
              {['residence', 'work', 'visit', 'investor', 'student', 'dependent', 'golden'].map((v) => (
                <option key={v} value={v} className="capitalize">{v}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Height (cm)</label>
            <input className="input" type="number" min={50} max={250} value={form.height_cm}
              onChange={(e) => setForm((f) => ({ ...f, height_cm: e.target.value }))} />
          </div>
          <div>
            <label className="label">Weight (kg)</label>
            <input className="input" type="number" min={1} max={300} value={form.weight_kg}
              onChange={(e) => setForm((f) => ({ ...f, weight_kg: e.target.value }))} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
          </div>
          <div>
            <label className="label">Phone</label>
            <input className="input" type="tel" value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))} />
          </div>
        </div>
        <div>
          <label className="label">Occupation</label>
          <input className="input" value={form.occupation}
            onChange={(e) => setForm((f) => ({ ...f, occupation: e.target.value }))} />
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

// ── Remarks Panel ──────────────────────────────────────────────────────────────

function RemarksPanel({ appId }: { appId: string }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [text, setText] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['remarks', appId],
    queryFn: () => applicationsApi.listRemarks(appId),
  })

  const remarks: Array<{ text: string; author: string; author_type: string; created_at: string }> =
    data?.data?.data ?? []

  const addRemark = useMutation({
    mutationFn: () => applicationsApi.addRemark(appId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remarks', appId] })
      toast('Remark added.')
      setText('')
    },
  })

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

  return (
    <div>
      <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
        <MessageSquare className="w-4 h-4 text-gray-400" /> Remarks
      </p>
      {isLoading
        ? <p className="text-xs text-gray-400">Loading...</p>
        : remarks.length === 0
          ? <p className="text-xs text-gray-400 italic">No remarks yet.</p>
          : (
            <div className="space-y-2 mb-3 max-h-48 overflow-y-auto">
              {remarks.map((r, i) => (
                <div key={i} className="bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-gray-700">{r.author}</span>
                    {roleBadge(r.author_type)}
                    <span className="text-xs text-gray-400 ml-auto">
                      {new Date(r.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{r.text}</p>
                </div>
              ))}
            </div>
          )}
      <div className="flex gap-2">
        <input className="input flex-1 text-sm" value={text} onChange={(e) => setText(e.target.value)}
          placeholder="Add a remark..." />
        <button className="btn-primary text-sm px-3" disabled={!text.trim() || addRemark.isPending}
          onClick={() => addRemark.mutate()}>
          Add
        </button>
      </div>
    </div>
  )
}

// ── Loadings Panel ─────────────────────────────────────────────────────────────

function LoadingsPanel({ appId, onRecalculate }: { appId: string; onRecalculate: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [form, setForm] = useState({ loading_type: 'underwriter', amount: '', percentage: '', notes: '' })
  const [showAdd, setShowAdd] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['loadings', appId],
    queryFn: () => applicationsApi.listLoadings(appId),
  })

  const loadings: Array<{ id: string; loading_type: string; amount: string; percentage: string; notes: string; applied_by: string }> =
    data?.data?.data ?? []

  const addLoading = useMutation({
    mutationFn: () => applicationsApi.addLoading(appId, {
      loading_type: form.loading_type,
      amount: form.amount ? Number(form.amount) : null,
      percentage: form.percentage ? Number(form.percentage) : null,
      notes: form.notes || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadings', appId] })
      toast('Loading applied.')
      setForm({ loading_type: 'underwriter', amount: '', percentage: '', notes: '' })
      setShowAdd(false)
      onRecalculate()
    },
  })

  const removeLoading = useMutation({
    mutationFn: (id: string) => applicationsApi.removeLoading(appId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loadings', appId] })
      toast('Loading removed.')
      onRecalculate()
    },
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
          <DollarSign className="w-4 h-4 text-gray-400" /> Underwriter Loadings
        </p>
        <button className="text-xs text-primary-600 hover:text-primary-700 font-medium"
          onClick={() => setShowAdd((s) => !s)}>
          + Add Loading
        </button>
      </div>

      {showAdd && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-gray-600 font-medium">Type</label>
              <select className="input text-sm" value={form.loading_type}
                onChange={(e) => setForm((f) => ({ ...f, loading_type: e.target.value }))}>
                {['underwriter', 'bmi', 'other', 'tpa', 'broker', 'insurer'].map((t) => (
                  <option key={t} value={t} className="capitalize">{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-600 font-medium">Amount (AED)</label>
              <input className="input text-sm" type="number" min={0} step="0.01" value={form.amount}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))} />
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-600 font-medium">Notes</label>
            <input className="input text-sm" value={form.notes}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} />
          </div>
          <div className="flex gap-2">
            <button className="btn-primary text-xs px-3" onClick={() => addLoading.mutate()}
              disabled={addLoading.isPending}>Apply</button>
            <button className="btn-secondary text-xs px-3" onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      )}

      {isLoading
        ? <p className="text-xs text-gray-400">Loading...</p>
        : loadings.length === 0
          ? <p className="text-xs text-gray-400 italic">No loadings applied.</p>
          : (
            <div className="rounded-lg border border-gray-200 overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    {['Type', 'Amount (AED)', 'Applied By', ''].map((h) => (
                      <th key={h} className="text-left px-3 py-2 font-medium text-gray-600">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {loadings.map((l) => (
                    <tr key={l.id}>
                      <td className="px-3 py-2 capitalize">{l.loading_type}</td>
                      <td className="px-3 py-2">{l.amount ? `AED ${Number(l.amount).toFixed(2)}` : `${l.percentage}%`}</td>
                      <td className="px-3 py-2 text-gray-500">{l.applied_by ?? '—'}</td>
                      <td className="px-3 py-2">
                        <button onClick={() => removeLoading.mutate(l.id)} className="text-red-400 hover:text-red-600">
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
    </div>
  )
}

// ── Document Downloads Panel ───────────────────────────────────────────────────

function DocumentsPanel({ appId }: { appId: string }) {
  const { toast } = useToast()

  async function download(fetchFn: () => Promise<{ data: Blob }>, filename: string) {
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

  const docs = [
    { label: 'Medical Application Form (MAF)', fn: () => documentsApi.generateMaf(appId), file: `MAF-${appId}.pdf` },
    { label: 'KYC Document', fn: () => documentsApi.generateKyc(appId), file: `KYC-${appId}.pdf` },
    { label: 'Table of Benefits (ToB)', fn: () => documentsApi.generateTob(appId), file: `TOB-${appId}.pdf` },
  ]

  return (
    <div>
      <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
        <Download className="w-4 h-4 text-gray-400" /> Documents
      </p>
      <div className="space-y-2">
        {docs.map((d) => (
          <button key={d.label}
            onClick={() => download(d.fn, d.file)}
            className="flex items-center gap-3 w-full text-left px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors text-sm text-gray-700">
            <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
            {d.label}
            <Download className="w-3.5 h-3.5 text-gray-400 ml-auto" />
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Application Detail Modal ───────────────────────────────────────────────────

function ApplicationDetailModal({ appId, onClose }: { appId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [showAddItem, setShowAddItem] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)
  const [showReject, setShowReject] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [activeTab, setActiveTab] = useState<'details' | 'loadings' | 'remarks' | 'docs'>('details')

  const { data, isLoading, error } = useQuery({
    queryKey: ['application', appId],
    queryFn: () => applicationsApi.get(appId),
  })

  const app = data?.data?.data ?? data?.data

  const submitMut = useMutation({
    mutationFn: () => applicationsApi.submit(appId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); queryClient.invalidateQueries({ queryKey: ['applications'] }); toast('Submitted for review.') },
  })
  const approveMut = useMutation({
    mutationFn: () => applicationsApi.approve(appId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); queryClient.invalidateQueries({ queryKey: ['applications'] }); toast('Application approved.') },
  })
  const rejectMut = useMutation({
    mutationFn: () => applicationsApi.reject(appId, rejectReason),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); queryClient.invalidateQueries({ queryKey: ['applications'] }); toast('Application rejected.'); setShowReject(false) },
  })
  const issueMut = useMutation({
    mutationFn: () => applicationsApi.issue(appId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); queryClient.invalidateQueries({ queryKey: ['applications'] }); toast('Policy issued!') },
  })
  const recalcMut = useMutation({
    mutationFn: () => applicationsApi.recalculate(appId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['application', appId] }); toast('Premium recalculated.') },
  })
  const removeMut = useMutation({
    mutationFn: (itemId: string) => applicationsApi.removeItem(appId, itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['application', appId] }),
  })
  const removeMemberMut = useMutation({
    mutationFn: (memberId: string) => membersApi.remove(appId, memberId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['application', appId] }),
  })

  const isWorking = submitMut.isPending || approveMut.isPending || rejectMut.isPending || issueMut.isPending

  const tabs = [
    { id: 'details', label: 'Details' },
    { id: 'loadings', label: 'Loadings' },
    { id: 'remarks', label: 'Remarks' },
    { id: 'docs', label: 'Documents' },
  ] as const

  return (
    <>
      <Modal open={true} onClose={onClose} title="Application Details" size="lg">
        {isLoading && <LoadingSpinner />}
        {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">Failed to load application.</div>}

        {app && (
          <div className="space-y-5">
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

            {/* Details Tab */}
            {activeTab === 'details' && (
              <>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  {([
                    ['Ref #', app.application_number],
                    ['Customer', app.customer_name],
                    ['Email', app.customer_email],
                    ['Members', String(app.member_count)],
                    ['Premium', `AED ${Number(app.total_premium).toFixed(2)}`],
                    ['Status', null],
                  ] as [string, string | null][]).map(([label, value]) => (
                    <div key={label} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">{label}</p>
                      {value !== null
                        ? <p className="font-medium text-gray-900">{value}</p>
                        : (
                          <div className="flex flex-wrap gap-1">
                            <StatusBadge status={app.status} />
                            {app.aml_status && app.aml_status !== 'clear' && <AmlBadge status={app.aml_status} />}
                            {app.govt_check_status && <GovtBadge status={app.govt_check_status} />}
                          </div>
                        )}
                    </div>
                  ))}
                </div>

                {/* Premium breakdown */}
                {app.premium_breakdown && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-blue-800">Premium Breakdown</p>
                      <button onClick={() => recalcMut.mutate()} disabled={recalcMut.isPending}
                        className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium">
                        <RefreshCw className="w-3 h-3" />
                        {recalcMut.isPending ? 'Calculating...' : 'Recalculate'}
                      </button>
                    </div>
                    <div className="space-y-1 text-xs">
                      {app.premium_breakdown.gross_premium_excl_tax && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Gross Premium (excl. VAT)</span>
                          <span className="font-medium">AED {app.premium_breakdown.gross_premium_excl_tax}</span>
                        </div>
                      )}
                      {app.premium_breakdown.vat_amount && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">VAT @ {((Number(app.premium_breakdown.vat_rate ?? 0.05)) * 100).toFixed(0)}%</span>
                          <span className="font-medium">AED {app.premium_breakdown.vat_amount}</span>
                        </div>
                      )}
                      {app.premium_breakdown.psp_fee && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Processing Fee</span>
                          <span className="font-medium">AED {app.premium_breakdown.psp_fee}</span>
                        </div>
                      )}
                      {app.premium_breakdown.amount_payable && (
                        <div className="flex justify-between border-t border-blue-200 pt-1 mt-1">
                          <span className="font-semibold text-gray-800">Total Payable</span>
                          <span className="font-bold text-blue-800">AED {app.premium_breakdown.amount_payable}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

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
                              {['Name', 'DOB / Age', 'Relationship', 'Gender', 'Emirates ID', ''].map((h) => (
                                <th key={h} className="text-left px-3 py-2 font-medium text-gray-600">{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {app.members.map((m: Member) => (
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
                                <td className="px-3 py-2 font-mono text-gray-500 text-xs">
                                  {(m as unknown as { emirates_id?: string }).emirates_id ?? '—'}
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
                            {app.items.map((item: ApplicationItem) => (
                              <tr key={item.id} className="hover:bg-gray-50">
                                <td className="px-3 py-2 font-medium text-gray-900">
                                  {item.coverage?.name ?? item.coverage_id.slice(0, 8)}
                                </td>
                                <td className="px-3 py-2 text-gray-500 capitalize">
                                  {item.coverage?.coverage_type?.replace(/_/g, ' ') ?? '—'}
                                </td>
                                <td className="px-3 py-2 text-gray-700">AED {Number(item.premium).toFixed(2)}</td>
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
              </>
            )}

            {/* Loadings Tab */}
            {activeTab === 'loadings' && (
              <LoadingsPanel appId={appId} onRecalculate={() => recalcMut.mutate()} />
            )}

            {/* Remarks Tab */}
            {activeTab === 'remarks' && <RemarksPanel appId={appId} />}

            {/* Documents Tab */}
            {activeTab === 'docs' && <DocumentsPanel appId={appId} />}
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

const STATUS_FILTERS = [
  { label: 'All', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Submitted', value: 'submitted' },
  { label: 'Approved', value: 'approved' },
  { label: 'Rejected', value: 'rejected' },
  { label: 'Issued', value: 'issued' },
]

const AML_FILTERS = [
  { label: 'All AML', value: '' },
  { label: 'Clear', value: 'clear' },
  { label: 'Flagged', value: 'flagged' },
  { label: 'Hold', value: 'hold' },
  { label: 'Cleared', value: 'cleared' },
]

const GOVT_FILTERS = [
  { label: 'All Govt', value: '' },
  { label: 'Pending', value: 'pending' },
  { label: 'Verified', value: 'verified' },
  { label: 'Failed', value: 'failed' },
]

export default function ApplicationsPage() {
  const [showNew, setShowNew] = useState(false)
  const [viewingId, setViewingId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [amlFilter, setAmlFilter] = useState('')
  const [govtFilter, setGovtFilter] = useState('')
  const [search, setSearch] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['applications', statusFilter, amlFilter, govtFilter],
    queryFn: () => applicationsApi.list(1, {
      status: statusFilter || undefined,
      aml_status: amlFilter || undefined,
      govt_check_status: govtFilter || undefined,
    }),
  })

  const allApps: AppRow[] = data?.data?.data ?? data?.data?.items ?? []
  const applications = allApps.filter((a) =>
    !search || a.customer_name.toLowerCase().includes(search.toLowerCase())
      || a.application_number.toLowerCase().includes(search.toLowerCase())
      || a.customer_email.toLowerCase().includes(search.toLowerCase()),
  )

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

      {/* Filter bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <input
          className="input w-56 text-sm"
          placeholder="Search by name or ref..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input w-36 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {STATUS_FILTERS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        <select className="input w-36 text-sm" value={amlFilter} onChange={(e) => setAmlFilter(e.target.value)}>
          {AML_FILTERS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        <select className="input w-36 text-sm" value={govtFilter} onChange={(e) => setGovtFilter(e.target.value)}>
          {GOVT_FILTERS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        {(statusFilter || amlFilter || govtFilter || search) && (
          <button className="text-sm text-gray-500 hover:text-gray-700"
            onClick={() => { setStatusFilter(''); setAmlFilter(''); setGovtFilter(''); setSearch('') }}>
            Clear filters
          </button>
        )}
      </div>

      {/* Quick filter chips */}
      <div className="mb-5 flex flex-wrap gap-2">
        {[
          { label: 'Pending Review', s: 'submitted', a: '', g: '' },
          { label: 'AML Hold', s: '', a: 'hold', g: '' },
          { label: 'AML Flagged', s: '', a: 'flagged', g: '' },
          { label: 'Govt Check Pending', s: '', a: '', g: 'pending' },
          { label: 'Issued', s: 'issued', a: '', g: '' },
        ].map((chip) => {
          const active = statusFilter === chip.s && amlFilter === chip.a && govtFilter === chip.g
          return (
            <button
              key={chip.label}
              onClick={() => { setStatusFilter(chip.s); setAmlFilter(chip.a); setGovtFilter(chip.g) }}
              className={`text-xs px-3 py-1 rounded-full border font-medium transition-colors ${
                active
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
              }`}
            >
              {chip.label}
            </button>
          )
        })}
      </div>

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load applications." />}

      {!isLoading && !error && applications.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <FileText className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No applications found</h3>
          <p className="text-sm text-gray-500 mb-4 max-w-sm">
            {statusFilter || amlFilter || govtFilter || search
              ? 'Try adjusting your filters.'
              : 'Create an application directly or convert a quote.'}
          </p>
          {!statusFilter && !amlFilter && !govtFilter && !search && (
            <button className="btn-primary" onClick={() => setShowNew(true)}>
              <Plus className="w-4 h-4" /> New Application
            </button>
          )}
        </div>
      )}

      {!isLoading && !error && applications.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Ref #', 'Customer', 'Email', 'Members', 'Premium', 'Status', 'AML', 'Govt Check', 'Created', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {applications.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{a.application_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{a.customer_name}</td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{a.customer_email}</td>
                  <td className="px-4 py-3 text-center text-gray-600">{a.member_count}</td>
                  <td className="px-4 py-3 text-gray-600">AED {Number(a.total_premium).toFixed(2)}</td>
                  <td className="px-4 py-3"><StatusBadge status={a.status} /></td>
                  <td className="px-4 py-3"><AmlBadge status={a.aml_status} /></td>
                  <td className="px-4 py-3"><GovtBadge status={a.govt_check_status} /></td>
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
