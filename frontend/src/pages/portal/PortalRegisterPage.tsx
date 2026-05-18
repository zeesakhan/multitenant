import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Heart, ArrowRight } from 'lucide-react'
import { portalAuthApi } from '../../services/portalApi'
import { setPortalAuth } from '../../store/portalAuthStore'

type Step = 'tenant' | 'identity' | 'account'

export default function PortalRegisterPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('tenant')
  const [tenantCode, setTenantCode] = useState('')
  const [tenantId, setTenantId] = useState('')
  const [tenantName, setTenantName] = useState('')
  const [policyNumber, setPolicyNumber] = useState('')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
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
      setStep('identity')
    } catch {
      setError('Company code not found. Please check and try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleIdentityNext(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (!policyNumber.trim() || !dateOfBirth) {
      setError('Policy number and date of birth are required.')
      return
    }
    setStep('account')
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      const res = await portalAuthApi.register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        policy_number: policyNumber.toUpperCase().trim(),
        date_of_birth: dateOfBirth,
      }, tenantId)
      const { access_token } = res.data.data
      // Set token in localStorage so the interceptor includes it in the /me request
      localStorage.setItem('portal_token', access_token)
      const meRes = await portalAuthApi.me()
      const user = meRes.data.data
      setPortalAuth(access_token, tenantId, user)
      navigate('/portal/dashboard')
    } catch (err: unknown) {
      localStorage.removeItem('portal_token')
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const steps = [
    { key: 'tenant', label: 'Company' },
    { key: 'identity', label: 'Verify' },
    { key: 'account', label: 'Account' },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Heart className="w-7 h-7 text-emerald-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Create Your Account</h1>
            <p className="text-gray-500 text-sm mt-1">Access your health insurance policy online</p>
          </div>

          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {steps.map((s, i) => (
              <div key={s.key} className="flex items-center gap-2">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                  step === s.key ? 'bg-emerald-600 text-white' :
                  steps.findIndex(x => x.key === step) > i ? 'bg-emerald-200 text-emerald-700' :
                  'bg-gray-100 text-gray-400'
                }`}>{i + 1}</div>
                <span className={`text-xs ${step === s.key ? 'text-emerald-700 font-medium' : 'text-gray-400'}`}>{s.label}</span>
                {i < steps.length - 1 && <div className="w-6 h-px bg-gray-200" />}
              </div>
            ))}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
          )}

          {step === 'tenant' && (
            <form onSubmit={handleTenantLookup} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Company Code</label>
                <input
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 uppercase tracking-wider"
                  value={tenantCode}
                  onChange={(e) => setTenantCode(e.target.value)}
                  placeholder="e.g. TESTCO"
                  required autoFocus
                />
                <p className="mt-1 text-xs text-gray-400">Found on your insurance policy or welcome letter</p>
              </div>
              <button type="submit" disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
                {loading ? 'Looking up…' : <>Continue <ArrowRight className="w-4 h-4" /></>}
              </button>
            </form>
          )}

          {step === 'identity' && (
            <form onSubmit={handleIdentityNext} className="space-y-5">
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800">
                <strong>{tenantName}</strong> — Enter your policy details to verify your identity.
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Policy Number</label>
                <input
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 uppercase"
                  value={policyNumber}
                  onChange={(e) => setPolicyNumber(e.target.value)}
                  placeholder="e.g. POL-20260001"
                  required autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth (primary insured)</label>
                <input
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  type="date"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  required
                />
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setStep('tenant')}
                  className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                  Back
                </button>
                <button type="submit"
                  className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors">
                  Verify <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          )}

          {step === 'account' && (
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First name</label>
                  <input className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    value={firstName} onChange={(e) => setFirstName(e.target.value)} required autoFocus />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last name</label>
                  <input className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    value={lastName} onChange={(e) => setLastName(e.target.value)} required />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email address</label>
                <input className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 characters" minLength={8} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm password</label>
                <input className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Repeat password" minLength={8} required />
              </div>
              <div className="flex gap-3 pt-1">
                <button type="button" onClick={() => setStep('identity')}
                  className="flex-1 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                  Back
                </button>
                <button type="submit" disabled={loading}
                  className="flex-1 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
                  {loading ? 'Creating…' : 'Create account'}
                </button>
              </div>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/portal/login" className="text-emerald-600 hover:text-emerald-700 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
