import { useState, FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { User, Lock, CheckCircle } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'
import { setPortalAuth, usePortalAuth } from '../../store/portalAuthStore'

export default function PortalProfilePage() {
  const qc = useQueryClient()
  const { tenantId, user: storedUser } = usePortalAuth()
  const [profileSuccess, setProfileSuccess] = useState(false)
  const [pwSuccess, setPwSuccess] = useState(false)
  const [pwError, setPwError] = useState('')

  const { data } = useQuery({ queryKey: ['portal-me'], queryFn: portalCustomerApi.me, retry: false })
  const profile = data?.data?.data ?? storedUser

  const [firstName, setFirstName] = useState(profile?.first_name ?? '')
  const [lastName, setLastName] = useState(profile?.last_name ?? '')
  const [phone, setPhone] = useState(profile?.phone ?? '')

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  const profileMutation = useMutation({
    mutationFn: () => portalCustomerApi.updateProfile({ first_name: firstName, last_name: lastName, phone: phone || undefined }),
    onSuccess: async () => {
      setProfileSuccess(true)
      const meRes = await portalCustomerApi.me()
      const updated = meRes.data.data
      if (tenantId && storedUser) {
        setPortalAuth(localStorage.getItem('portal_token')!, tenantId, updated)
      }
      qc.invalidateQueries({ queryKey: ['portal-me'] })
      setTimeout(() => setProfileSuccess(false), 3000)
    },
  })

  const pwMutation = useMutation({
    mutationFn: () => portalCustomerApi.changePassword(currentPw, newPw),
    onSuccess: () => {
      setPwSuccess(true)
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
      setTimeout(() => setPwSuccess(false), 3000)
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setPwError(msg ?? 'Password change failed.')
    },
  })

  function handleProfileSubmit(e: FormEvent) {
    e.preventDefault()
    profileMutation.mutate()
  }

  function handlePwSubmit(e: FormEvent) {
    e.preventDefault()
    setPwError('')
    if (newPw !== confirmPw) { setPwError('Passwords do not match.'); return }
    if (newPw.length < 8) { setPwError('New password must be at least 8 characters.'); return }
    pwMutation.mutate()
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
        <p className="text-gray-500 text-sm mt-1">Update your personal information and password.</p>
      </div>

      <div className="max-w-xl space-y-6">
        {/* Personal info */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-5">
            <User className="w-4 h-4 text-gray-400" /> Personal Information
          </h2>

          {profileSuccess && (
            <div className="mb-4 flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              <CheckCircle className="w-4 h-4" /> Profile updated successfully.
            </div>
          )}

          <form onSubmit={handleProfileSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First name</label>
                <input
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last name</label>
                <input
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
              <input
                className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-gray-50 text-gray-500 cursor-not-allowed"
                value={profile?.email ?? ''}
                disabled
              />
              <p className="mt-1 text-xs text-gray-400">Email cannot be changed. Contact your insurer.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone number</label>
              <input
                className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 555 000 0000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Policy number</label>
              <input
                className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-gray-50 text-gray-500 cursor-not-allowed font-mono"
                value={profile?.policy_id ? '(linked)' : '—'}
                disabled
              />
            </div>
            <button
              type="submit"
              disabled={profileMutation.isPending}
              className="w-full py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {profileMutation.isPending ? 'Saving…' : 'Save Changes'}
            </button>
          </form>
        </div>

        {/* Change password */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-5">
            <Lock className="w-4 h-4 text-gray-400" /> Change Password
          </h2>

          {pwSuccess && (
            <div className="mb-4 flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
              <CheckCircle className="w-4 h-4" /> Password changed successfully.
            </div>
          )}
          {pwError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{pwError}</div>
          )}

          <form onSubmit={handlePwSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Current password</label>
              <input
                className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">New password</label>
              <input
                className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                minLength={8}
                placeholder="Min 8 characters"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm new password</label>
              <input
                className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                minLength={8}
                required
              />
            </div>
            <button
              type="submit"
              disabled={pwMutation.isPending}
              className="w-full py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {pwMutation.isPending ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
