import { useState, FormEvent } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { Heart, Plus, Trash2, CheckCircle, ArrowRight, ArrowLeft, ShieldCheck, Users, FileText } from 'lucide-react'
import { buyApiService, MemberInput } from '../../services/buyApi'

const RELATIONSHIP_OPTIONS = [
  { value: 'spouse', label: 'Spouse' },
  { value: 'child', label: 'Child' },
  { value: 'parent', label: 'Parent' },
  { value: 'sibling', label: 'Sibling' },
  { value: 'dependent', label: 'Other Dependent' },
]

const GENDER_OPTIONS = [
  { value: 'M', label: 'Male' },
  { value: 'F', label: 'Female' },
  { value: 'O', label: 'Other' },
  { value: 'U', label: 'Prefer not to say' },
]

const PREMIUM_FACTORS: Record<string, number> = {
  self: 1.0, spouse: 0.75, parent: 0.70, sibling: 0.65, child: 0.35, dependent: 0.40,
}

const RELATIONSHIP_LABELS: Record<string, string> = {
  self: 'Primary Insured', spouse: 'Spouse', child: 'Child',
  parent: 'Parent', sibling: 'Sibling', dependent: 'Other Dependent',
}

function fmt(n: number | string) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

interface DepForm {
  first_name: string; last_name: string; date_of_birth: string
  relationship: 'spouse' | 'child' | 'parent' | 'sibling' | 'dependent'; gender: 'M' | 'F' | 'O' | 'U'
}

interface QuoteResult {
  total_premium: number
  breakdown: { relationship: string; first_name: string; last_name: string; premium: number }[]
  coverages: { name: string; coverage_type: string; limit_amount: string | null }[]
}

interface Confirmation {
  application_number: string
  total_premium: number
  plan_name: string
  product_name: string
  member_count: number
}

const STEPS = ['Personal Info', 'Dependents', 'Review & Quote', 'Confirmation']

export default function BuyApplyPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as {
    tenantId: string; tenantName: string
    plan: { id: string; name: string; base_premium: string; coverages: { name: string; coverage_type: string; limit_amount: string | null }[] }
    productName: string
  } | null

  const [step, setStep] = useState(0)

  // Step 1: primary member
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [dob, setDob] = useState('')
  const [gender, setGender] = useState<'M' | 'F' | 'O' | 'U'>('M')
  const [step1Error, setStep1Error] = useState('')

  // Step 2: dependents
  const [dependents, setDependents] = useState<DepForm[]>([])
  const [addingDep, setAddingDep] = useState(false)
  const [depForm, setDepForm] = useState<DepForm>({
    first_name: '', last_name: '', date_of_birth: '',
    relationship: 'spouse', gender: 'M',
  })

  // Step 3: quote
  const [quote, setQuote] = useState<QuoteResult | null>(null)
  const [quoteLoading, setQuoteLoading] = useState(false)
  const [quoteError, setQuoteError] = useState('')

  // Step 4: submit
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [confirmation, setConfirmation] = useState<Confirmation | null>(null)

  if (!state) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-500 mb-4">No plan selected.</p>
          <Link to="/buy" className="text-emerald-600 hover:underline font-medium">Start over</Link>
        </div>
      </div>
    )
  }

  const { tenantId, tenantName, plan, productName } = state

  function buildMembers(): MemberInput[] {
    const primary: MemberInput = {
      first_name: firstName, last_name: lastName,
      date_of_birth: dob, relationship: 'self', gender,
    }
    return [primary, ...dependents.map((d) => ({
      first_name: d.first_name, last_name: d.last_name,
      date_of_birth: d.date_of_birth,
      relationship: d.relationship as MemberInput['relationship'],
      gender: d.gender as MemberInput['gender'],
    }))]
  }

  // Local quote calculation (no server round-trip for UI)
  function calcLocalQuote(): QuoteResult {
    const base = parseFloat(plan.base_premium)
    const members = buildMembers()
    const breakdown = members.map((m) => ({
      relationship: m.relationship,
      first_name: m.first_name,
      last_name: m.last_name,
      premium: Math.round(base * (PREMIUM_FACTORS[m.relationship] ?? 0.5) * 100) / 100,
    }))
    return {
      total_premium: Math.round(breakdown.reduce((s, b) => s + b.premium, 0) * 100) / 100,
      breakdown,
      coverages: plan.coverages,
    }
  }

  function handleStep1Submit(e: FormEvent) {
    e.preventDefault()
    setStep1Error('')
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !dob) {
      setStep1Error('All fields except phone are required.')
      return
    }
    setStep(1)
  }

  function addDependent() {
    if (!depForm.first_name || !depForm.last_name || !depForm.date_of_birth) return
    setDependents((prev) => [...prev, { ...depForm }])
    setDepForm({ first_name: '', last_name: '', date_of_birth: '', relationship: 'spouse', gender: 'M' })
    setAddingDep(false)
  }

  function removeDependent(i: number) {
    setDependents((prev) => prev.filter((_, idx) => idx !== i))
  }

  async function proceedToReview() {
    setQuoteLoading(true)
    setQuoteError('')
    try {
      const res = await buyApiService.getQuote(tenantId, plan.id, buildMembers())
      setQuote(res.data.data)
      setStep(2)
    } catch {
      setQuoteError('Failed to calculate quote. Please try again.')
    } finally {
      setQuoteLoading(false)
    }
  }

  async function handleSubmit() {
    setSubmitting(true)
    setSubmitError('')
    try {
      const res = await buyApiService.submitApplication(tenantId, {
        plan_id: plan.id,
        members: buildMembers(),
        email: email.trim(),
        phone: phone.trim() || undefined,
      })
      setConfirmation(res.data.data)
      setStep(3)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setSubmitError(msg ?? 'Failed to submit application. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 bg-white border-b border-gray-200 sticky top-0 z-10">
        <Link to="/buy" className="flex items-center gap-2">
          <Heart className="w-5 h-5 text-emerald-600" />
          <span className="font-bold text-gray-900">HealthShield</span>
        </Link>
        <span className="text-sm text-gray-500">{tenantName}</span>
      </nav>

      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Plan summary chip */}
        <div className="flex items-center gap-3 mb-6 p-3 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-gray-800 truncate">{plan.name}</p>
            <p className="text-xs text-gray-400">{productName} · from ${fmt(plan.base_premium)}/yr</p>
          </div>
          <button
            onClick={() => navigate(-1)}
            className="text-xs text-emerald-600 hover:underline font-medium flex-shrink-0"
          >
            Change
          </button>
        </div>

        {/* Step indicator */}
        {step < 3 && (
          <div className="flex items-center mb-8">
            {STEPS.slice(0, 3).map((s, i) => (
              <div key={s} className="flex items-center flex-1">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors ${
                  step === i ? 'bg-emerald-600 text-white' :
                  step > i ? 'bg-emerald-200 text-emerald-700' : 'bg-gray-100 text-gray-400'
                }`}>{i + 1}</div>
                <span className={`ml-2 text-xs hidden sm:block ${step === i ? 'text-emerald-700 font-semibold' : 'text-gray-400'}`}>{s}</span>
                {i < 2 && <div className="flex-1 h-px bg-gray-200 mx-3" />}
              </div>
            ))}
          </div>
        )}

        {/* ── Step 0: Personal Info ──────────────────────────────────────── */}
        {step === 0 && (
          <form onSubmit={handleStep1Submit} className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
            <h2 className="text-lg font-bold text-gray-900 mb-2">Your Personal Information</h2>

            {step1Error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{step1Error}</div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First name *</label>
                <input className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={firstName} onChange={(e) => setFirstName(e.target.value)} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last name *</label>
                <input className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={lastName} onChange={(e) => setLastName(e.target.value)} required />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email address *</label>
              <input type="email" className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone number</label>
              <input type="tel" className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 555 000 0000" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of birth *</label>
                <input type="date" className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={dob} onChange={(e) => setDob(e.target.value)} required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                <select className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={gender} onChange={(e) => setGender(e.target.value as 'M' | 'F' | 'O' | 'U')}>
                  {GENDER_OPTIONS.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
                </select>
              </div>
            </div>
            <button type="submit"
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors mt-2">
              Next: Add Dependents <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        )}

        {/* ── Step 1: Dependents ────────────────────────────────────────── */}
        {step === 1 && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-1">Add Family Members</h2>
            <p className="text-sm text-gray-400 mb-5">Optional — add dependents you want covered under this plan.</p>

            {/* Current primary */}
            <div className="flex items-center gap-3 p-3 bg-emerald-50 rounded-xl border border-emerald-200 mb-4">
              <div className="w-8 h-8 bg-emerald-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                {firstName[0]}{lastName[0]}
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{firstName} {lastName}</p>
                <p className="text-xs text-emerald-700">Primary Insured</p>
              </div>
              <span className="ml-auto text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                ${fmt(parseFloat(plan.base_premium))}/yr
              </span>
            </div>

            {/* Dependent list */}
            {dependents.length > 0 && (
              <div className="space-y-2 mb-4">
                {dependents.map((d, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 text-xs font-bold">
                      {d.first_name[0]}{d.last_name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{d.first_name} {d.last_name}</p>
                      <p className="text-xs text-gray-400">{RELATIONSHIP_LABELS[d.relationship]}</p>
                    </div>
                    <span className="text-xs text-gray-500">
                      ${fmt(parseFloat(plan.base_premium) * (PREMIUM_FACTORS[d.relationship] ?? 0.5))}/yr
                    </span>
                    <button onClick={() => removeDependent(i)} className="text-red-400 hover:text-red-600 p-1">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Add dependent form */}
            {addingDep ? (
              <div className="border border-dashed border-emerald-300 rounded-xl p-4 space-y-3 mb-4 bg-emerald-50/40">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">First name</label>
                    <input className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      value={depForm.first_name} onChange={(e) => setDepForm((f) => ({ ...f, first_name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Last name</label>
                    <input className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      value={depForm.last_name} onChange={(e) => setDepForm((f) => ({ ...f, last_name: e.target.value }))} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Relationship</label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      value={depForm.relationship} onChange={(e) => setDepForm((f) => ({ ...f, relationship: e.target.value as DepForm['relationship'] }))}>
                      {RELATIONSHIP_OPTIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Gender</label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      value={depForm.gender} onChange={(e) => setDepForm((f) => ({ ...f, gender: e.target.value as 'M' | 'F' | 'O' | 'U' }))}>
                      {GENDER_OPTIONS.map((g) => <option key={g.value} value={g.value}>{g.label}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Date of birth</label>
                  <input type="date" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    value={depForm.date_of_birth} onChange={(e) => setDepForm((f) => ({ ...f, date_of_birth: e.target.value }))} />
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setAddingDep(false)}
                    className="flex-1 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors">
                    Cancel
                  </button>
                  <button onClick={addDependent}
                    disabled={!depForm.first_name || !depForm.last_name || !depForm.date_of_birth}
                    className="flex-1 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
                    Add Member
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setAddingDep(true)}
                className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-300 rounded-xl text-sm text-gray-500 hover:border-emerald-400 hover:text-emerald-600 transition-colors mb-4"
              >
                <Plus className="w-4 h-4" /> Add a Dependent
              </button>
            )}

            {/* Quote preview */}
            <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 mb-4 text-sm">
              <div className="flex justify-between text-gray-500 mb-1">
                <span className="flex items-center gap-1"><Users className="w-3.5 h-3.5" /> {1 + dependents.length} member{(1 + dependents.length) !== 1 ? 's' : ''}</span>
                <span className="font-bold text-gray-900">${fmt(calcLocalQuote().total_premium)}/yr</span>
              </div>
              <p className="text-xs text-gray-400">Estimated premium · final quote on next step</p>
            </div>

            {quoteError && (
              <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{quoteError}</div>
            )}

            <div className="flex gap-3">
              <button onClick={() => setStep(0)}
                className="flex items-center gap-1 px-4 py-2.5 border border-gray-300 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button onClick={proceedToReview} disabled={quoteLoading}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
                {quoteLoading ? 'Calculating…' : <><span>Review Quote</span><ArrowRight className="w-4 h-4" /></>}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 2: Review & Quote ────────────────────────────────────── */}
        {step === 2 && quote && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Review Your Quote</h2>

              {/* Premium total */}
              <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-xl border border-emerald-200 mb-4">
                <div>
                  <p className="text-sm text-emerald-700 font-medium">Annual Premium</p>
                  <p className="text-xs text-emerald-600">{quote.breakdown.length} member{quote.breakdown.length !== 1 ? 's' : ''} covered</p>
                </div>
                <p className="text-3xl font-extrabold text-emerald-700">${fmt(quote.total_premium)}</p>
              </div>

              {/* Members breakdown */}
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Member Breakdown</h3>
              <div className="space-y-2 mb-4">
                {quote.breakdown.map((b, i) => (
                  <div key={i} className="flex items-center justify-between text-sm py-2 border-b border-gray-100 last:border-0">
                    <span className="text-gray-700">{b.first_name} {b.last_name}
                      <span className="text-xs text-gray-400 ml-2 capitalize">{RELATIONSHIP_LABELS[b.relationship] ?? b.relationship}</span>
                    </span>
                    <span className="font-semibold text-gray-900">${fmt(b.premium)}</span>
                  </div>
                ))}
              </div>

              {/* Coverages */}
              {quote.coverages.length > 0 && (
                <>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">What's Covered</h3>
                  <div className="space-y-1.5">
                    {quote.coverages.map((c, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                        <span className="font-medium">{c.name}</span>
                        {c.limit_amount && <span className="ml-auto text-gray-400">up to ${fmt(c.limit_amount)}</span>}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Applicant summary */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
              <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
                <FileText className="w-4 h-4 text-gray-400" /> Application Summary
              </h3>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                <dt className="text-gray-400">Name</dt>
                <dd className="font-medium text-gray-900">{firstName} {lastName}</dd>
                <dt className="text-gray-400">Email</dt>
                <dd className="font-medium text-gray-900 truncate">{email}</dd>
                {phone && <><dt className="text-gray-400">Phone</dt><dd className="font-medium text-gray-900">{phone}</dd></>}
                <dt className="text-gray-400">Plan</dt>
                <dd className="font-medium text-gray-900">{plan.name}</dd>
                <dt className="text-gray-400">Product</dt>
                <dd className="font-medium text-gray-900">{productName}</dd>
              </dl>
            </div>

            {submitError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{submitError}</div>
            )}

            <div className="flex gap-3">
              <button onClick={() => setStep(1)}
                className="flex items-center gap-1 px-4 py-2.5 border border-gray-300 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors">
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button onClick={handleSubmit} disabled={submitting}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors">
                {submitting ? 'Submitting…' : 'Submit Application'}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Confirmation ─────────────────────────────────────── */}
        {step === 3 && confirmation && (
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-emerald-600" />
            </div>
            <h2 className="text-2xl font-extrabold text-gray-900 mb-1">Application Submitted!</h2>
            <p className="text-gray-500 text-sm mb-6">
              Our team will review your application and contact you at <strong>{email}</strong> within 1–2 business days.
            </p>

            <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 mb-6 text-left space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Application #</span>
                <span className="font-mono font-bold text-gray-900">{confirmation.application_number}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Plan</span>
                <span className="font-medium text-gray-900">{confirmation.plan_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Members</span>
                <span className="font-medium text-gray-900">{confirmation.member_count}</span>
              </div>
              <div className="flex justify-between text-sm border-t border-gray-200 pt-2 mt-2">
                <span className="text-gray-600 font-medium">Annual Premium</span>
                <span className="font-bold text-emerald-700 text-lg">${fmt(confirmation.total_premium)}</span>
              </div>
            </div>

            <div className="space-y-2 mb-6 text-left">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">What happens next?</p>
              {[
                'Our underwriting team reviews your application (1–2 business days)',
                'You receive an approval email with your policy number',
                'Register on the Member Portal using your policy number + date of birth',
                'Access your policy, file claims, and manage your coverage online',
              ].map((step, i) => (
                <div key={i} className="flex items-start gap-3 text-sm text-gray-600">
                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/portal/register"
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors"
              >
                Register on Portal <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/buy"
                className="flex-1 py-2.5 border border-gray-300 text-gray-600 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors text-center"
              >
                Back to Home
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
