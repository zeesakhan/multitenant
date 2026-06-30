import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Shield, Search } from 'lucide-react'
import api, { authApi } from '../services/api'
import { setAuth } from '../store/authStore'

type Step = 'tenant' | 'credentials'

export default function LoginPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('tenant')
  const [tenantCode, setTenantCode] = useState('ADAMJEE')
  const [tenantId, setTenantId] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [email, setEmail] = useState('admin@adamjee.ae')
  const [password, setPassword] = useState('adamjee123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleTenantLookup = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await api.get(`/auth/tenant/${tenantCode.trim().toUpperCase()}`)
      const { id, name } = res.data?.data ?? res.data
      setTenantId(id)
      setTenantName(name)
      setStep('credentials')
    } catch {
      setError('Tenant not found. Check the tenant code and try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    // Store tenantId before the request so the interceptor picks it up
    localStorage.setItem('tenantId', tenantId)
    try {
      const res = await authApi.login(email, password)
      const payload = res.data?.data ?? res.data
      const { access_token } = payload
      // Store token temporarily so /auth/me request is authenticated
      localStorage.setItem('token', access_token)
      const meRes = await authApi.me()
      const user = meRes.data?.data ?? meRes.data
      setAuth(access_token, tenantId, user)
      navigate('/')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { errors?: { message: string }[] } } })
        ?.response?.data?.errors?.[0]?.message
      setError(msg ?? 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 to-primary-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 rounded-2xl mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Health Insurance</h1>
          <p className="text-primary-200 mt-1">Platform Administration</p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {step === 'tenant' ? (
            <>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Find your organisation</h2>
              <p className="text-sm text-gray-500 mb-6">Enter your tenant code to continue</p>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
              )}

              <form onSubmit={handleTenantLookup} className="space-y-4">
                <div>
                  <label className="label">Tenant Code</label>
                  <input
                    type="text"
                    className="input uppercase font-mono tracking-widest"
                    value={tenantCode}
                    onChange={(e) => setTenantCode(e.target.value.toUpperCase())}
                    placeholder="e.g. ADAMJEE"
                    required
                    autoFocus
                  />
                  <p className="mt-1 text-xs text-gray-400">
                    Demo: <strong>ADAMJEE</strong> (Adamjee Insurance) · <strong>TESTCO</strong> (SafeLife Insurance)
                  </p>
                </div>
                <button type="submit" className="btn-primary w-full justify-center py-2.5" disabled={loading}>
                  <Search className="w-4 h-4" />
                  {loading ? 'Looking up...' : 'Continue'}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-6 p-3 bg-primary-50 rounded-lg">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center text-white text-xs font-bold">
                  {tenantName[0]}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{tenantName}</p>
                  <button onClick={() => { setStep('tenant'); setError('') }} className="text-xs text-primary-600 hover:underline">
                    Change organisation
                  </button>
                </div>
              </div>

              <h2 className="text-xl font-semibold text-gray-900 mb-6">Sign in</h2>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
              )}

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="label">Email address</label>
                  <input
                    type="email"
                    className="input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoFocus
                  />
                </div>
                <div>
                  <label className="label">Password</label>
                  <input
                    type="password"
                    className="input"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="btn-primary w-full justify-center py-2.5" disabled={loading}>
                  {loading ? 'Signing in...' : 'Sign in'}
                </button>
                <div className="text-center">
                  <Link to="/forgot-password" className="text-sm text-primary-600 hover:text-primary-700">
                    Forgot password?
                  </Link>
                </div>
              </form>
              <p className="mt-4 text-center text-xs text-gray-400">
                ADAMJEE: admin@adamjee.ae / adamjee123<br />
                Broker: broker@adamjee.ae · Underwriter: underwriter@adamjee.ae
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
