import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Package, Layers, ShieldCheck } from 'lucide-react'
import { productsApi, plansApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { Product, Plan } from '../types'

const PLAN_TYPES = ['individual', 'family', 'group', 'senior']
const COVERAGE_TYPES = [
  'hospitalization', 'outpatient', 'dental', 'vision', 'maternity',
  'mental_health', 'prescription', 'preventive', 'emergency', 'wellness',
]

function planTypeBadge(type: string) {
  const colors: Record<string, string> = {
    individual: 'bg-blue-100 text-blue-700',
    family: 'bg-purple-100 text-purple-700',
    group: 'bg-orange-100 text-orange-700',
    senior: 'bg-teal-100 text-teal-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[type] ?? 'bg-gray-100 text-gray-600'}`}>
      {type}
    </span>
  )
}

function errMsg(err: unknown) {
  const d = (err as { response?: { data?: { errors?: { message: string }[] } } })?.response?.data
  return d?.errors?.[0]?.message ?? 'Something went wrong.'
}

function AddProductModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ name: '', code: '', description: '', status: 'draft' })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => productsApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      onClose()
      setForm({ name: '', code: '', description: '', status: 'draft' })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title="Add New Product">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Product Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.name} onChange={set('name')}
              placeholder="e.g. Basic Health Plan" required />
          </div>
          <div>
            <label className="label">Product Code <span className="text-red-500">*</span></label>
            <input className="input uppercase font-mono" value={form.code} onChange={set('code')}
              placeholder="e.g. BASIC-HEALTH" required />
            <p className="mt-1 text-xs text-gray-400">Unique identifier — letters, numbers, hyphens</p>
          </div>
        </div>
        <div>
          <label className="label">Description</label>
          <textarea className="input resize-none" rows={3} value={form.description}
            onChange={set('description')} placeholder="Brief description of this product..." />
        </div>
        <div>
          <label className="label">Initial Status</label>
          <select className="input" value={form.status} onChange={set('status')}>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create Product'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function AddPlanModal({ open, onClose, productId }: { open: boolean; onClose: () => void; productId: string }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    name: '', code: '', plan_type: 'individual', base_premium: '', description: '', is_active: true,
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => plansApi.create(productId, {
      ...form,
      base_premium: parseFloat(form.base_premium),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans', productId] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      onClose()
      setForm({ name: '', code: '', plan_type: 'individual', base_premium: '', description: '', is_active: true })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title="Add New Plan" level={2}>
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Plan Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.name} onChange={set('name')}
              placeholder="e.g. Basic Individual" required />
          </div>
          <div>
            <label className="label">Plan Code <span className="text-red-500">*</span></label>
            <input className="input uppercase font-mono" value={form.code} onChange={set('code')}
              placeholder="e.g. BASIC-IND" required />
            <p className="mt-1 text-xs text-gray-400">Unique within this product</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Plan Type <span className="text-red-500">*</span></label>
            <select className="input" value={form.plan_type} onChange={set('plan_type')}>
              {PLAN_TYPES.map((t) => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Base Premium <span className="text-red-500">*</span></label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
              <input className="input pl-7" type="number" min="0.01" step="0.01"
                value={form.base_premium} onChange={set('base_premium')} placeholder="0.00" required />
            </div>
          </div>
        </div>
        <div>
          <label className="label">Description</label>
          <textarea className="input resize-none" rows={2} value={form.description}
            onChange={set('description')} placeholder="Optional plan description..." />
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="plan_is_active" checked={form.is_active}
            onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
            className="w-4 h-4 rounded border-gray-300" />
          <label htmlFor="plan_is_active" className="text-sm text-gray-700">
            Active — available for quoting immediately
          </label>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create Plan'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function AddCoverageModal({ open, onClose, productId, planId, planName }: {
  open: boolean; onClose: () => void; productId: string; planId: string; planName: string
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    name: '', coverage_type: 'hospitalization', limit_amount: '', copay: '', coinsurance_percent: '',
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => plansApi.addCoverage(productId, planId, {
      name: form.name,
      coverage_type: form.coverage_type,
      limit_amount: form.limit_amount ? parseFloat(form.limit_amount) : null,
      copay: form.copay ? parseFloat(form.copay) : null,
      coinsurance_percent: form.coinsurance_percent ? parseFloat(form.coinsurance_percent) : null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans', productId] })
      onClose()
      setForm({ name: '', coverage_type: 'hospitalization', limit_amount: '', copay: '', coinsurance_percent: '' })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title={`Add Coverage — ${planName}`} level={2}>
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div>
          <label className="label">Coverage Name <span className="text-red-500">*</span></label>
          <input className="input" value={form.name} onChange={set('name')}
            placeholder="e.g. Inpatient Hospitalization" required />
        </div>
        <div>
          <label className="label">Coverage Type <span className="text-red-500">*</span></label>
          <select className="input" value={form.coverage_type} onChange={set('coverage_type')}>
            {COVERAGE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="label">Limit Amount</label>
            <input className="input" type="number" min="0" step="0.01"
              value={form.limit_amount} onChange={set('limit_amount')} placeholder="e.g. 100000" />
          </div>
          <div>
            <label className="label">Copay ($)</label>
            <input className="input" type="number" min="0" step="0.01"
              value={form.copay} onChange={set('copay')} placeholder="e.g. 50" />
          </div>
          <div>
            <label className="label">Coinsurance %</label>
            <input className="input" type="number" min="0" max="100" step="0.01"
              value={form.coinsurance_percent} onChange={set('coinsurance_percent')} placeholder="e.g. 20" />
          </div>
        </div>
        <p className="text-xs text-gray-400">All fields optional — leave blank if not applicable.</p>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Adding...' : 'Add Coverage'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function ProductPlansModal({ product, onClose }: { product: Product; onClose: () => void }) {
  const [showAddPlan, setShowAddPlan] = useState(false)
  const [coveragePlan, setCoveragePlan] = useState<Plan | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['plans', product.id],
    queryFn: () => plansApi.list(product.id),
  })

  const plans: Plan[] = data?.data?.data ?? data?.data?.items ?? []

  return (
    <>
      <Modal open={true} onClose={onClose} title={`Plans — ${product.name}`} size="xl">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">{(product as Product & { code?: string }).code}</span>
            <StatusBadge status={product.status} />
          </div>
          <button className="btn-primary text-sm" onClick={() => setShowAddPlan(true)}>
            <Plus className="w-4 h-4" /> Add Plan
          </button>
        </div>

        {isLoading && <LoadingSpinner />}
        {error && <ErrorMessage message="Failed to load plans." />}

        {!isLoading && !error && plans.length === 0 && (
          <div className="flex flex-col items-center py-14 text-center border border-dashed border-gray-200 rounded-xl">
            <Layers className="w-10 h-10 text-gray-300 mb-3" />
            <p className="text-sm text-gray-500 mb-1">No plans yet</p>
            <p className="text-xs text-gray-400 max-w-xs">
              Add your first plan to enable quoting for this product.
            </p>
          </div>
        )}

        {!isLoading && !error && plans.length > 0 && (
          <div className="rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Plan Name', 'Code', 'Type', 'Base Premium', 'Coverages', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {plans.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{p.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{p.code}</td>
                    <td className="px-4 py-3">{planTypeBadge(p.plan_type)}</td>
                    <td className="px-4 py-3 text-gray-700 font-medium">${Number(p.base_premium).toFixed(2)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                        {p.coverages?.length ?? 0}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        p.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {p.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setCoveragePlan(p)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" /> Add Coverage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Modal>

      <AddPlanModal open={showAddPlan} onClose={() => setShowAddPlan(false)} productId={product.id} />
      {coveragePlan && (
        <AddCoverageModal
          open={true}
          onClose={() => setCoveragePlan(null)}
          productId={product.id}
          planId={coveragePlan.id}
          planName={coveragePlan.name}
        />
      )}
    </>
  )
}

export default function ProductsPage() {
  const [showAdd, setShowAdd] = useState(false)
  const [plansProduct, setPlansProduct] = useState<Product | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.list(1),
  })

  const products: Product[] = data?.data?.data ?? data?.data?.items ?? []

  return (
    <div className="p-8">
      <PageHeader
        title="Products"
        subtitle="Insurance products and plan configurations"
        action={
          <button className="btn-primary" onClick={() => setShowAdd(true)}>
            <Plus className="w-4 h-4" /> Add Product
          </button>
        }
      />

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load products." />}

      {!isLoading && !error && products.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <Package className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">No products yet</h3>
          <p className="text-sm text-gray-500 mb-4 max-w-sm">
            Add your first insurance product to get started.
          </p>
          <button className="btn-primary" onClick={() => setShowAdd(true)}>
            <Plus className="w-4 h-4" /> Add Product
          </button>
        </div>
      )}

      {!isLoading && !error && products.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Name', 'Code', 'Status', 'Plans', 'Created', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 bg-emerald-100 rounded-lg">
                        <Package className="w-3.5 h-3.5 text-emerald-600" />
                      </div>
                      <span className="font-medium text-gray-900">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{p.code ?? '—'}</td>
                  <td className="px-4 py-3"><StatusBadge status={p.status} /></td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-sm font-medium text-gray-700">
                      {p.plans?.length ?? 0}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setPlansProduct(p)}
                      className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                    >
                      <Layers className="w-3.5 h-3.5" /> View Plans
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AddProductModal open={showAdd} onClose={() => setShowAdd(false)} />
      {plansProduct && <ProductPlansModal product={plansProduct} onClose={() => setPlansProduct(null)} />}
    </div>
  )
}
