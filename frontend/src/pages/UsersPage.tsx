import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { usersApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { User } from '../types'

const USER_TYPES = ['agent', 'broker', 'customer', 'underwriter', 'claims_manager', 'tenant_admin']

function AddUserModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '',
    password: '', user_type: 'agent', phone: '',
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => usersApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      onClose()
      setForm({ first_name: '', last_name: '', email: '', password: '', user_type: 'agent', phone: '' })
      setError('')
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: { errors?: { message: string }[] } } })?.response?.data
      setError(d?.errors?.[0]?.message ?? 'Failed to create user.')
    },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={open} onClose={onClose} title="Add New User">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.first_name} onChange={set('first_name')} required />
          </div>
          <div>
            <label className="label">Last Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.last_name} onChange={set('last_name')} required />
          </div>
        </div>
        <div>
          <label className="label">Email Address <span className="text-red-500">*</span></label>
          <input className="input" type="email" value={form.email} onChange={set('email')} required />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Password <span className="text-red-500">*</span></label>
            <input className="input" type="password" value={form.password} onChange={set('password')}
              required minLength={8} placeholder="Min 8 characters" />
          </div>
          <div>
            <label className="label">Phone</label>
            <input className="input" value={form.phone} onChange={set('phone')} placeholder="+1 555 000 0000" />
          </div>
        </div>
        <div>
          <label className="label">User Type</label>
          <select className="input" value={form.user_type} onChange={set('user_type')}>
            {USER_TYPES.map((t) => (
              <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating...' : 'Create User'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function EditUserModal({ user, onClose }: { user: User; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    first_name: user.first_name, last_name: user.last_name,
    user_type: user.user_type, status: user.status,
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: () => usersApi.update(user.id, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      onClose()
    },
    onError: (err: unknown) => {
      const d = (err as { response?: { data?: { errors?: { message: string }[] } } })?.response?.data
      setError(d?.errors?.[0]?.message ?? 'Failed to update user.')
    },
  })

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Modal open={true} onClose={onClose} title={`Edit — ${user.first_name} ${user.last_name}`}>
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name</label>
            <input className="input" value={form.first_name} onChange={set('first_name')} required />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input className="input" value={form.last_name} onChange={set('last_name')} required />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">User Type</label>
            <select className="input" value={form.user_type} onChange={set('user_type')}>
              {USER_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Status</label>
            <select className="input" value={form.status} onChange={set('status')}>
              {['active', 'inactive', 'locked'].map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function UsersPage() {
  const [showAdd, setShowAdd] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list(1),
  })

  const users: User[] = data?.data?.data ?? data?.data?.items ?? data?.data ?? []

  return (
    <div className="p-8">
      <PageHeader
        title="Users"
        subtitle="Manage platform users and their roles"
        action={
          <button className="btn-primary" onClick={() => setShowAdd(true)}>
            <Plus className="w-4 h-4" /> Add User
          </button>
        }
      />

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load users." />}

      {!isLoading && !error && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Name', 'Email', 'Type', 'Status', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-10 text-center text-gray-400">No users found</td></tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900">{u.first_name} {u.last_name}</td>
                    <td className="px-4 py-3 text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className="badge badge-blue">{u.user_type?.replace(/_/g, ' ')}</span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={u.status} /></td>
                    <td className="px-4 py-3">
                      <button onClick={() => setEditing(u)}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                        Edit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      <AddUserModal open={showAdd} onClose={() => setShowAdd(false)} />
      {editing && <EditUserModal user={editing} onClose={() => setEditing(null)} />}
    </div>
  )
}
