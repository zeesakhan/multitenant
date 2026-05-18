import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Lock } from 'lucide-react'
import { tenantsApi } from '../services/api'
import { useAuth } from '../store/authStore'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { useToast } from '../context/ToastContext'
import { Tenant } from '../types'

const TIMEZONES = ['UTC', 'America/New_York', 'America/Chicago', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Dubai', 'Asia/Karachi', 'Asia/Kolkata', 'Asia/Singapore']
const CURRENCIES = ['USD', 'EUR', 'GBP', 'PKR', 'INR', 'AED', 'SGD', 'CAD', 'AUD']

function AddTenantModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const { toast } = useToast()
  const [form, setForm] = useState({
    code: '', name: '', contact_email: '', contact_phone: '',
    country: '', currency: 'USD', timezone: 'UTC',
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => tenantsApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
      toast('Tenant created.')
      onClose()
      setForm({ code: '', name: '', contact_email: '', contact_phone: '', country: '', currency: 'USD', timezone: 'UTC' })
      setError('')
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })
        ?.response?.data
      setError(msg?.errors?.[0]?.message ?? msg?.detail ?? 'Failed to create tenant.')
    },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setError('')
    mutation.mutate()
  }

  return (
    <Modal open={open} onClose={onClose} title="Add New Tenant">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Tenant Code <span className="text-red-500">*</span></label>
            <input className="input uppercase font-mono" value={form.code}
              onChange={set('code')} placeholder="e.g. ACMECORP" required maxLength={20} />
            <p className="mt-1 text-xs text-gray-400">Unique identifier — letters & numbers only</p>
          </div>
          <div>
            <label className="label">Company Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.name} onChange={set('name')}
              placeholder="Acme Insurance Co." required />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Contact Email</label>
            <input className="input" type="email" value={form.contact_email}
              onChange={set('contact_email')} placeholder="admin@company.com" />
          </div>
          <div>
            <label className="label">Contact Phone</label>
            <input className="input" value={form.contact_phone}
              onChange={set('contact_phone')} placeholder="+1 555 000 0000" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="label">Country</label>
            <input className="input" value={form.country} onChange={set('country')} placeholder="US" maxLength={3} />
          </div>
          <div>
            <label className="label">Currency</label>
            <select className="input" value={form.currency} onChange={set('currency')}>
              {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Timezone</label>
            <select className="input" value={form.timezone} onChange={set('timezone')}>
              {TIMEZONES.map((tz) => <option key={tz}>{tz}</option>)}
            </select>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create Tenant'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function TenantsPage() {
  const [showAdd, setShowAdd] = useState(false)
  const { user } = useAuth()
  const isSuperAdmin = user?.user_type === 'super_admin'

  const { data, isLoading, error } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => tenantsApi.list(1),
    enabled: isSuperAdmin,
  })

  const tenants: Tenant[] = data?.data?.items ?? data?.data?.data ?? []

  return (
    <div className="p-8">
      <PageHeader
        title="Tenants"
        subtitle="Manage insurance company tenants on this platform"
        action={
          isSuperAdmin ? (
            <button className="btn-primary" onClick={() => setShowAdd(true)}>
              <Plus className="w-4 h-4" /> Add Tenant
            </button>
          ) : null
        }
      />

      {!isSuperAdmin && (
        <div className="card flex items-center gap-3 text-amber-700 bg-amber-50 border-amber-200">
          <Lock className="w-5 h-5 flex-shrink-0" />
          <div>
            <p className="font-medium text-sm">Super Admin access required</p>
            <p className="text-xs mt-0.5">
              Log in as <strong>SYSTEM / superadmin@system.com / super123</strong> to manage tenants.
            </p>
          </div>
        </div>
      )}

      {isSuperAdmin && isLoading && <LoadingSpinner />}
      {isSuperAdmin && error && <ErrorMessage message="Failed to load tenants." />}

      {isSuperAdmin && !isLoading && !error && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Name', 'Code', 'Status', 'Currency', 'Timezone', 'Created'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tenants.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-gray-400">No tenants found</td>
                </tr>
              ) : (
                tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{t.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">{t.code}</td>
                    <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                    <td className="px-4 py-3 text-gray-600">{t.currency}</td>
                    <td className="px-4 py-3 text-gray-600">{t.timezone}</td>
                    <td className="px-4 py-3 text-gray-500">
                      {t.created_at ? new Date(t.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <AddTenantModal open={showAdd} onClose={() => setShowAdd(false)} />
    </div>
  )
}
