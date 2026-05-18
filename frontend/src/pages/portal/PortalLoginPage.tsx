import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Heart, ArrowRight } from 'lucide-react'
import { portalAuthApi } from '../../services/portalApi'
import { setPortalAuth } from '../../store/portalAuthStore'

type Step = 'tenant' | 'credentials'

export default function PortalLoginPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('tenant')
  const [tenantCode, setTenantCode] = useState('')
  const [tenantId, setTenantId] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleTenantLookup(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await portalAuthApi.resolveTenant(tenantCode.trim().toUpperCase())
      const { id, name } = res.data.data
      setTenantId(id)
      setTenantName(name)
      localStorage.setItem('portal_tenantId', id)
      setStep('credentials')
    } catch {
      setError('Company code not found. Please check and try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await portalAuthApi.login(email, password, tenantId)
      const { access_token } = res.data.data
      // Set token in localStorage so the interceptor includes it in the /me request
      localStorage.setItem('portal_token', access_token)
      const meRes = await portalAuthApi.me()
      const user = meRes.data.data
      if (user.user_type !== 'customer') {
        localStorage.removeItem('portal_token')
        setError('This portal is for policyholders only. Please use the staff portal.')
        setLoading(false)
        return
      }
      setPortalAuth(access_token, tenantId, user)
      navigate('/portal/dashboard')
    } catch (err: unknown) {
      localStorage.removeItem('portal_token')
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Heart className="w-7 h-7 text-emerald-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Member Portal</h1>
            <p className="text-gray-500 text-sm mt-1">
              {step === 'tenant' ? 'Enter your insurance company code to continue' : `Sign in to ${tenantName}`}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
          )}

          {step === 'tenant' ? (
            <form onSubmit={handleTenantLookup} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Code</label>
                <input
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent uppercase tracking-wider"
                  value={tenantCode}
                  onChange={(e) => setTenantCode(e.target.value)}
                  placeholder="e.g. TESTCO"
                  required
                  autoFocus
                />
                <p className="mt-1 text-xs text-gray-400">Found on your insurance policy documents</p>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Looking up…' : <>Continue <ArrowRight className="w-4 h-4" /></>}
              </button>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
                <input
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Your password"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Signing in…' : 'Sign in'}
              </button>
              <button
                type="button"
                onClick={() => { setStep('tenant'); setError('') }}
                className="w-full text-center text-sm text-gray-500 hover:text-gray-700"
              >
                ← Change company
              </button>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-gray-500">
            New member?{' '}
            <Link to="/portal/register" className="text-emerald-600 hover:text-emerald-700 font-medium">
              Create your account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
