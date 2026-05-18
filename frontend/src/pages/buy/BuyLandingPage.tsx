import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Heart, ArrowRight, ShieldCheck, Users, FileText, Phone } from 'lucide-react'
import axios from 'axios'

export default function BuyLandingPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await axios.get(`/api/v1/auth/tenant/${code.trim().toUpperCase()}`)
      const { id, name } = res.data.data
      navigate('/buy/products', { state: { tenantId: id, tenantName: name } })
    } catch {
      setError('Company code not found. Please check with your insurer.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-white/60 bg-white/70 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Heart className="w-6 h-6 text-emerald-600" />
          <span className="font-bold text-gray-900">HealthShield</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <Link to="/portal/login" className="text-gray-500 hover:text-gray-700">Member Login</Link>
          <Link to="/login" className="text-gray-500 hover:text-gray-700">Staff Login</Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <ShieldCheck className="w-3.5 h-3.5" /> Comprehensive Health Insurance
        </div>
        <h1 className="text-5xl font-extrabold text-gray-900 leading-tight mb-4">
          Protect your family's <br />
          <span className="text-emerald-600">health & future</span>
        </h1>
        <p className="text-gray-500 text-lg max-w-xl mx-auto mb-12">
          Browse plans, get an instant quote, and apply online in minutes.
          No paperwork. No hassle.
        </p>

        {/* Company code card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 max-w-md mx-auto">
          <h2 className="text-lg font-semibold text-gray-800 mb-1">Get Started</h2>
          <p className="text-sm text-gray-400 mb-5">Enter your insurance company code to see available plans</p>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 uppercase tracking-wider font-mono"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="e.g. ACME"
              required
              autoFocus
            />
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1 px-5 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Finding…' : <><span>Browse</span><ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>
          <p className="mt-3 text-xs text-gray-400">
            Already have a policy?{' '}
            <Link to="/portal/login" className="text-emerald-600 hover:underline font-medium">Sign in to your portal</Link>
          </p>
        </div>
      </div>

      {/* Feature grid */}
      <div className="max-w-5xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              icon: ShieldCheck,
              color: 'bg-emerald-100 text-emerald-600',
              title: 'Comprehensive Coverage',
              desc: 'Hospitalization, outpatient, dental, vision, maternity and more.',
            },
            {
              icon: Users,
              color: 'bg-blue-100 text-blue-600',
              title: 'Family Plans',
              desc: 'Cover your spouse, children, and parents under one affordable plan.',
            },
            {
              icon: FileText,
              color: 'bg-violet-100 text-violet-600',
              title: 'Easy Claims',
              desc: 'Submit claims online anytime and track them in real time.',
            },
          ].map(({ icon: Icon, color, title, desc }) => (
            <div key={title} className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${color}`}>
                <Icon className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
              <p className="text-sm text-gray-500">{desc}</p>
            </div>
          ))}
        </div>

        {/* Help */}
        <div className="mt-8 flex items-center justify-center gap-2 text-sm text-gray-400">
          <Phone className="w-4 h-4" />
          Need help? Contact your insurance agent for your company code.
        </div>
      </div>
    </div>
  )
}
