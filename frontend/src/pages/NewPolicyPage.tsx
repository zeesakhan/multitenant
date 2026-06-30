import { useState, useRef, useEffect } from 'react'
import {
  ChevronDown, ChevronUp, Plus, X, Check, Loader2, AlertCircle,
  FileText, Download, Upload, Eye, MessageSquare, CheckCircle,
} from 'lucide-react'
import api, { applicationsApi, membersApi, documentsApi } from '../services/api'
import { useToast } from '../context/ToastContext'
import DocumentScanner, { type ScanResult } from '../components/DocumentScanner'

// ── Types ────────────────────────────────────────────────────────────────────

type Gender = 'male' | 'female'
type Relationship = 'self' | 'spouse' | 'child' | 'parent' | 'sibling' | 'dependent'

interface MemberRow {
  relationship: Relationship
  first_name: string; last_name: string; email: string; phone: string
  date_of_birth: string; gender: Gender
  nationality: string; height_cm: string; weight_kg: string
  marital_status: string
  emirates_id: string; document_expiry: string; passport_number: string
  q_hypertension: boolean; q_diabetes: boolean
  q_covid: boolean; q_covid_complications: boolean
  q_medical_treatment: boolean; q_medical_details: string
  q_pregnant: boolean; q_pregnancy_weeks: string
}

interface WizardForm {
  sponsor_type: 'individual' | 'corporate'; trn: string
  insure_who: 'self' | 'family_without_self' | 'both'
  existing_policy: 'active_policy' | 'expired_gt30' | 'expired_lt30' | 'none'
  policy_start_date: string
  any_medication: boolean; any_pregnancy: boolean
  is_diplomatic_passport: boolean; is_eid_under_process: boolean
  members: MemberRow[]
  product_id: string; plan_id: string; plan_name: string
  cover_amount: string
  copay_opt_pct: string; copay_pharmacy_pct: string
  copay_lab_pct: string; copay_physio_pct: string
  quoted_total: number
  application_id: string; application_number: string
}

interface PlanCard {
  id: string; name: string; code: string; plan_type: string
  base_premium: string; description: string
  coverages: { id: string; name: string; coverage_type: string; limit_amount: string | null; copay: string | null }[]
  product_id: string; product_name: string
}

interface RemarkItem { text: string; author_name: string; author_role: string; created_at: string }
interface UploadedDoc { filename: string }

// ── Constants ─────────────────────────────────────────────────────────────────

const NATIONALITIES = [
  'UAE National', 'Pakistani', 'Indian', 'Filipino', 'Bangladeshi', 'Egyptian',
  'Jordanian', 'Saudi Arabian', 'British', 'American', 'Sri Lankan', 'Nepali',
  'Lebanese', 'Syrian', 'Yemeni', 'Ethiopian', 'Sudanese', 'Chinese',
  'Malaysian', 'Indonesian', 'Turkish', 'Iranian', 'Kenyan', 'Nigerian',
  'South African', 'Ghanaian', 'Moroccan', 'Algerian', 'Libyan', 'Iraqi',
  'Kuwaiti', 'Bahraini', 'Qatari', 'Omani', 'Afghan', 'German', 'French',
  'Spanish', 'Italian', 'Russian', 'South Korean', 'Japanese', 'Australian',
  'Canadian', 'New Zealander', 'Tunisian', 'Ugandan', 'Tanzanian', 'Other',
]

const COVER_AMOUNTS = [
  { value: '150000', label: 'AED 150,000' },
  { value: '250000', label: 'AED 250,000' },
  { value: '500000', label: 'AED 500,000' },
  { value: '1000000', label: 'AED 1,000,000' },
]

const COPAY_OPTIONS = ['0', '5', '10', '15', '20', '25']

const MEDICAL_QUESTIONS = [
  { id: 'hypertension', label: 'Suffering from hypertension / high blood pressure?' },
  { id: 'diabetes', label: 'Suffering from diabetes or insulin-dependent conditions?' },
  { id: 'covid_positive', label: 'Ever tested positive for COVID-19?' },
  { id: 'covid_complications', label: 'Any ongoing COVID-19 complications under medical monitoring?' },
  { id: 'medical_treatment', label: 'Under any medical observation or undergoing medical/surgical treatment?', hasDetails: true },
]

const EID_PATTERN = /^784-\d{4}-\d{7}-\d$/

const EMPTY_MEMBER: MemberRow = {
  relationship: 'spouse', first_name: '', last_name: '', email: '', phone: '',
  date_of_birth: '', gender: 'male',
  nationality: '', height_cm: '', weight_kg: '',
  marital_status: '',
  emirates_id: '', document_expiry: '', passport_number: '',
  q_hypertension: false, q_diabetes: false, q_covid: false,
  q_covid_complications: false, q_medical_treatment: false, q_medical_details: '',
  q_pregnant: false, q_pregnancy_weeks: '',
}

const INITIAL_FORM: WizardForm = {
  sponsor_type: 'individual', trn: '',
  insure_who: 'both',
  existing_policy: 'none',
  policy_start_date: '',
  any_medication: false, any_pregnancy: false,
  is_diplomatic_passport: false, is_eid_under_process: false,
  members: [{
    ...EMPTY_MEMBER, relationship: 'self', gender: 'male',
    first_name: '', last_name: '', email: '', phone: '',
  }],
  product_id: '', plan_id: '', plan_name: '',
  cover_amount: '', copay_opt_pct: '', copay_pharmacy_pct: '', copay_lab_pct: '', copay_physio_pct: '',
  quoted_total: 0,
  application_id: '', application_number: '',
}

const STEPS = [
  { num: 1, label: 'Applicant Details' },
  { num: 2, label: 'Get Quotes' },
  { num: 3, label: 'Additional Info' },
  { num: 4, label: 'Finalize' },
  { num: 5, label: 'Submit' },
]

// ── Helper: medical questionnaire builder ────────────────────────────────────

function buildMedicalQ(m: MemberRow) {
  return [
    { question_id: 'hypertension', answer: m.q_hypertension, details: null },
    { question_id: 'diabetes', answer: m.q_diabetes, details: null },
    { question_id: 'covid_positive', answer: m.q_covid, details: null },
    { question_id: 'covid_complications', answer: m.q_covid_complications, details: null },
    { question_id: 'medical_treatment', answer: m.q_medical_treatment,
      details: m.q_medical_treatment ? m.q_medical_details : null },
  ]
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {STEPS.map((s, i) => (
        <div key={s.num} className="flex items-center gap-1 flex-shrink-0">
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors ${
            current === s.num ? 'bg-primary-700 text-white' :
            current > s.num ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-400'
          }`}>
            {current > s.num
              ? <Check className="w-3 h-3" />
              : <span className="w-3 text-center leading-none">{s.num}</span>}
            <span className="hidden sm:inline">{s.label}</span>
          </div>
          {i < STEPS.length - 1 && <div className="w-3 h-px bg-gray-200 flex-shrink-0" />}
        </div>
      ))}
    </div>
  )
}

function Field({ label, value, onChange, type = 'text', placeholder, required }: {
  label: string; value: string; onChange: (v: string) => void
  type?: string; placeholder?: string; required?: boolean
}) {
  return (
    <div>
      <label className="label">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
      <input className="input" type={type} value={value}
        onChange={e => onChange(e.target.value)} placeholder={placeholder} />
    </div>
  )
}

function SelectField({ label, value, onChange, options, placeholder, required }: {
  label: string; value: string; onChange: (v: string) => void
  options: { value: string; label: string }[] | string[]
  placeholder?: string; required?: boolean
}) {
  const normalised = (options as (string | { value: string; label: string })[]).map(o =>
    typeof o === 'string' ? { value: o, label: o } : o
  )
  return (
    <div>
      <label className="label">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
      <select className="input" value={value} onChange={e => onChange(e.target.value)}>
        <option value="">{placeholder ?? 'Select…'}</option>
        {normalised.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

function GenderToggle({ value, onChange }: { value: Gender; onChange: (v: Gender) => void }) {
  return (
    <div>
      <label className="label">Gender<span className="text-red-500 ml-0.5">*</span></label>
      <div className="flex gap-2">
        {(['male', 'female'] as Gender[]).map(g => (
          <button key={g} type="button" onClick={() => onChange(g)}
            className={`flex-1 py-2 rounded-lg border text-sm font-medium capitalize transition-colors ${
              value === g ? 'border-primary-600 bg-primary-50 text-primary-700' : 'border-gray-300 text-gray-600 hover:border-gray-400'
            }`}>
            {g === 'male' ? '♂ Male' : '♀ Female'}
          </button>
        ))}
      </div>
    </div>
  )
}

function YesNo({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-700">{label}</span>
      <div className="flex gap-1.5 flex-shrink-0 ml-4">
        {[true, false].map(v => (
          <button key={String(v)} type="button" onClick={() => onChange(v)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-colors ${
              value === v
                ? v ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-400 bg-gray-100 text-gray-700'
                : 'border-gray-200 text-gray-400 hover:border-gray-300'
            }`}>
            {v ? 'Yes' : 'No'}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Member block used in both Step 1 (basic) and Step 3 (docs) ───────────────

function MemberBasicFields({ member, onChange }: {
  member: MemberRow
  onChange: (k: keyof MemberRow, v: string | boolean | Gender | Relationship) => void
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <Field label="First Name" value={member.first_name} onChange={v => onChange('first_name', v)} required />
      <Field label="Last Name" value={member.last_name} onChange={v => onChange('last_name', v)} required />
      <div>
        <label className="label">Date of Birth<span className="text-red-500 ml-0.5">*</span></label>
        <input className="input" type="date" value={member.date_of_birth}
          onChange={e => onChange('date_of_birth', e.target.value)}
          max={new Date().toISOString().split('T')[0]} />
      </div>
      <GenderToggle value={member.gender} onChange={v => onChange('gender', v)} />
      <SelectField label="Nationality" value={member.nationality} onChange={v => onChange('nationality', v)}
        options={NATIONALITIES} required />
      <div className="grid grid-cols-2 gap-2">
        <Field label="Height (cm)" value={member.height_cm} onChange={v => onChange('height_cm', v)} type="number" placeholder="170" />
        <Field label="Weight (kg)" value={member.weight_kg} onChange={v => onChange('weight_kg', v)} type="number" placeholder="70" />
      </div>
    </div>
  )
}

// ── Step 1: Applicant Details ────────────────────────────────────────────────

function Step1({ form, setForm }: { form: WizardForm; setForm: (f: WizardForm) => void }) {
  const set = (k: keyof WizardForm, v: unknown) => setForm({ ...form, [k]: v })

  const principal = form.members[0]
  const setPrincipal = (k: keyof MemberRow, v: string | boolean | Gender | Relationship) => {
    const members = [...form.members]
    members[0] = { ...members[0], [k]: v }
    setForm({ ...form, members })
  }

  const setMember = (i: number, k: keyof MemberRow, v: string | boolean | Gender | Relationship) => {
    const members = [...form.members]
    members[i] = { ...members[i], [k]: v }
    setForm({ ...form, members })
  }

  const addMember = () => setForm({ ...form, members: [...form.members, { ...EMPTY_MEMBER }] })

  const removeMember = (i: number) =>
    setForm({ ...form, members: form.members.filter((_, idx) => idx !== i) })

  return (
    <div className="space-y-6">
      {/* Sponsor type */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Sponsorship</h3>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {(['individual', 'corporate'] as const).map(t => (
            <button key={t} type="button" onClick={() => set('sponsor_type', t)}
              className={`py-2.5 rounded-lg border text-sm font-medium capitalize transition-colors ${
                form.sponsor_type === t ? 'border-primary-600 bg-primary-50 text-primary-700' : 'border-gray-300 text-gray-600'
              }`}>
              {t}
            </button>
          ))}
        </div>
        {form.sponsor_type === 'corporate' && (
          <Field label="Tax Registration Number (TRN)" value={form.trn}
            onChange={v => set('trn', v)} placeholder="100-XXXXXXXXX-XXXXX" />
        )}
      </div>

      {/* Who to insure */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Who to Insure</h3>
        <div className="space-y-1">
          {[
            { v: 'self', l: 'Self Only' },
            { v: 'family_without_self', l: 'Family (Excluding Self)' },
            { v: 'both', l: 'Self + Family' },
          ].map(({ v, l }) => (
            <label key={v} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
              form.insure_who === v ? 'bg-primary-50 border border-primary-200' : 'hover:bg-gray-50'
            }`}>
              <input type="radio" name="insure_who" value={v}
                checked={form.insure_who === v}
                onChange={() => set('insure_who', v)}
                className="text-primary-600" />
              <span className="text-sm">{l}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Existing policy */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Existing Health Insurance in UAE</h3>
        <div className="space-y-1">
          {[
            { v: 'active_policy', l: 'Active policy currently' },
            { v: 'expired_gt30', l: 'Expired more than 30 days ago' },
            { v: 'expired_lt30', l: 'Expired within the last 30 days' },
            { v: 'none', l: 'No existing policy' },
          ].map(({ v, l }) => (
            <label key={v} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
              form.existing_policy === v ? 'bg-primary-50 border border-primary-200' : 'hover:bg-gray-50'
            }`}>
              <input type="radio" name="existing_policy" value={v}
                checked={form.existing_policy === v}
                onChange={() => set('existing_policy', v as WizardForm['existing_policy'])}
                className="text-primary-600" />
              <span className="text-sm">{l}</span>
            </label>
          ))}
        </div>
        <div className="mt-4">
          <label className="label">Policy Start Date</label>
          <input className="input" type="date" value={form.policy_start_date}
            onChange={e => set('policy_start_date', e.target.value)}
            min={new Date().toISOString().split('T')[0]} />
        </div>
      </div>

      {/* Principal */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Principal Member</h3>
        <MemberBasicFields member={principal} onChange={(k, v) => setPrincipal(k, v)} />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
          <Field label="Email" value={principal.email} onChange={v => setPrincipal('email', v)}
            type="email" placeholder="member@email.com" required />
          <Field label="Phone" value={principal.phone} onChange={v => setPrincipal('phone', v)}
            type="tel" placeholder="+971 5X XXX XXXX" />
        </div>
      </div>

      {/* Family members */}
      {form.members.slice(1).map((m, idx) => {
        const i = idx + 1
        return (
          <div key={i} className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700 capitalize">
                Family Member {idx + 1}
                {m.first_name && <span className="text-gray-400 font-normal"> — {m.first_name}</span>}
              </h3>
              <button type="button" onClick={() => removeMember(i)}
                className="p-1 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="mb-4">
              <SelectField label="Relationship" value={m.relationship}
                onChange={v => setMember(i, 'relationship', v as Relationship)}
                options={['spouse', 'child', 'parent', 'sibling', 'dependent']} />
            </div>
            <MemberBasicFields member={m} onChange={(k, v) => setMember(i, k, v)} />
          </div>
        )
      })}

      <button type="button" onClick={addMember}
        className="w-full py-3 border-2 border-dashed border-primary-300 text-primary-700 rounded-xl text-sm font-semibold hover:bg-primary-50 transition-colors flex items-center justify-center gap-2">
        <Plus className="w-4 h-4" /> Add Family Member
      </button>

      {/* Pre-existing flags */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-1">Health Declarations</h3>
        <p className="text-xs text-gray-400 mb-3">These affect premium rating. Accurate answers ensure the right quote.</p>
        <YesNo
          label="Do any members take regular medication or have a chronic condition?"
          value={form.any_medication}
          onChange={v => set('any_medication', v)}
        />
        <YesNo
          label="Is any female member currently pregnant or planning a family?"
          value={form.any_pregnancy}
          onChange={v => set('any_pregnancy', v)}
        />
      </div>
    </div>
  )
}

// ── Step 2: Get Quotes ────────────────────────────────────────────────────────

function Step2({ form, setForm, onPlanSelected }: {
  form: WizardForm; setForm: (f: WizardForm) => void
  onPlanSelected: (planId: string, productId: string, planName: string, total: number) => void
}) {
  const [plans, setPlans] = useState<PlanCard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [quotingPlanId, setQuotingPlanId] = useState('')
  const [expandedPlan, setExpandedPlan] = useState<string | null>(null)

  const set = (k: keyof WizardForm, v: unknown) => setForm({ ...form, [k]: v })

  useEffect(() => {
    api.get('/buy/products')
      .then(r => {
        const products: any[] = r.data.data ?? []
        const flat: PlanCard[] = products.flatMap(p =>
          (p.plans ?? []).map((pl: any) => ({ ...pl, product_id: p.id, product_name: p.name }))
        )
        setPlans(flat)
      })
      .catch(() => setError('Failed to load plans. Please refresh.'))
      .finally(() => setLoading(false))
  }, [])

  const filteredPlans = plans.filter(p => {
    if (form.cover_amount) {
      const limit = p.coverages.find(c => c.coverage_type === 'hospitalization')?.limit_amount
      if (limit && Number(limit) < Number(form.cover_amount)) return false
    }
    return true
  })

  const handleSelect = async (plan: PlanCard) => {
    setQuotingPlanId(plan.id)
    try {
      const members = form.members.map(m => ({
        first_name: m.first_name || 'Member',
        last_name: m.last_name || 'N',
        date_of_birth: m.date_of_birth || '1990-01-01',
        relationship: m.relationship,
        gender: m.gender,
      }))
      const res = await api.post('/buy/quote', { plan_id: plan.id, members })
      const total: number = res.data.data?.total_premium ?? 0
      onPlanSelected(plan.id, plan.product_id, plan.name, total)
    } catch {
      setError('Failed to get quote for this plan. Please try again.')
    } finally {
      setQuotingPlanId('')
    }
  }

  const fmt = (n: number | string) => Number(n).toLocaleString('en-AE', { minimumFractionDigits: 0, maximumFractionDigits: 0 })

  return (
    <div className="space-y-5">
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />{error}
        </div>
      )}

      {/* Filters */}
      <div className="card p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Filter Plans</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <SelectField label="Annual Limit" value={form.cover_amount}
            onChange={v => set('cover_amount', v)} options={COVER_AMOUNTS} placeholder="Any" />
          <div>
            <label className="label">Co-pay GP</label>
            <select className="input" value={form.copay_opt_pct} onChange={e => set('copay_opt_pct', e.target.value)}>
              <option value="">Any</option>
              {COPAY_OPTIONS.map(o => <option key={o} value={o}>{o}%</option>)}
            </select>
          </div>
          <div>
            <label className="label">Co-pay Pharmacy</label>
            <select className="input" value={form.copay_pharmacy_pct} onChange={e => set('copay_pharmacy_pct', e.target.value)}>
              <option value="">Any</option>
              {COPAY_OPTIONS.map(o => <option key={o} value={o}>{o}%</option>)}
            </select>
          </div>
          <div>
            <label className="label">Co-pay Lab</label>
            <select className="input" value={form.copay_lab_pct} onChange={e => set('copay_lab_pct', e.target.value)}>
              <option value="">Any</option>
              {COPAY_OPTIONS.map(o => <option key={o} value={o}>{o}%</option>)}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          <span className="ml-3 text-gray-500">Loading plans…</span>
        </div>
      ) : filteredPlans.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No plans match your filter. Try adjusting the filters above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredPlans.map(plan => {
            const isExpanded = expandedPlan === plan.id
            const isQuoting = quotingPlanId === plan.id
            const hospCoverage = plan.coverages.find(c => c.coverage_type === 'hospitalization')
            return (
              <div key={plan.id} className="card p-5 flex flex-col gap-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-gray-900">{plan.name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{plan.product_name} · {plan.plan_type}</p>
                    {plan.description && <p className="text-xs text-gray-500 mt-1">{plan.description}</p>}
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xl font-bold text-primary-700">AED {fmt(plan.base_premium)}</p>
                    <p className="text-xs text-gray-400">/yr base</p>
                  </div>
                </div>

                {hospCoverage?.limit_amount && (
                  <p className="text-xs text-gray-600">
                    Annual limit: <strong>AED {fmt(hospCoverage.limit_amount)}</strong>
                  </p>
                )}

                <button type="button" onClick={() => setExpandedPlan(isExpanded ? null : plan.id)}
                  className="flex items-center gap-1 text-xs text-primary-600 font-medium hover:text-primary-700">
                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  {isExpanded ? 'Hide' : 'Show'} {plan.coverages.length} coverages
                </button>

                {isExpanded && (
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1">
                    {plan.coverages.map(c => (
                      <div key={c.id} className="flex items-start gap-2 text-xs text-gray-600">
                        <CheckCircle className="w-3.5 h-3.5 text-green-500 mt-0.5 flex-shrink-0" />
                        <span>
                          <strong>{c.name}</strong>
                          {c.limit_amount ? ` — AED ${fmt(c.limit_amount)}` : ''}
                          {c.copay ? ` · ${c.copay}% co-pay` : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                <button type="button" onClick={() => handleSelect(plan)} disabled={isQuoting}
                  className="mt-auto btn-primary flex items-center justify-center gap-2 py-2.5">
                  {isQuoting
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Getting quote…</>
                    : 'Select This Plan'}
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Step 3: Additional Info ───────────────────────────────────────────────────

function Step3({ form, setForm }: { form: WizardForm; setForm: (f: WizardForm) => void }) {
  const [openIdx, setOpenIdx] = useState<number | null>(0)
  const [eidErrors, setEidErrors] = useState<Record<number, string>>({})

  const set = (k: keyof WizardForm, v: unknown) => setForm({ ...form, [k]: v })

  const setMember = (i: number, k: keyof MemberRow, v: string | boolean) => {
    const members = [...form.members]
    members[i] = { ...members[i], [k]: v }
    setForm({ ...form, members })
  }

  const validateEid = (i: number, val: string) => {
    if (val && !EID_PATTERN.test(val)) {
      setEidErrors(e => ({ ...e, [i]: 'Format: 784-YYYY-NNNNNNN-C' }))
    } else {
      setEidErrors(e => { const n = { ...e }; delete n[i]; return n })
    }
  }

  return (
    <div className="space-y-5">
      {/* Application-level UAE compliance */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-1">UAE Compliance Flags</h3>
        <p className="text-xs text-gray-400 mb-3">These apply to the application as a whole.</p>
        <YesNo
          label="Any member holds a diplomatic passport?"
          value={form.is_diplomatic_passport}
          onChange={v => set('is_diplomatic_passport', v)}
        />
        <YesNo
          label="Emirates ID currently under processing (not yet issued)?"
          value={form.is_eid_under_process}
          onChange={v => set('is_eid_under_process', v)}
        />
      </div>

      {/* Per-member accordion */}
      {form.members.map((m, i) => (
        <div key={i} className="card overflow-hidden">
          <button type="button" onClick={() => setOpenIdx(openIdx === i ? null : i)}
            className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                m.first_name ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-400'
              }`}>{i + 1}</span>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">
                  {m.first_name ? `${m.first_name} ${m.last_name}` : `Member ${i + 1}`}
                </p>
                <p className="text-xs text-gray-400 capitalize">{m.relationship}</p>
              </div>
            </div>
            {openIdx === i ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
          </button>

          {openIdx === i && (
            <div className="px-5 pb-5 space-y-5 border-t border-gray-100">
              {/* OCR document scan — auto-fills identity fields below */}
              <div className="pt-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Auto-fill from Document</p>
                <DocumentScanner
                  label={`Scan passport or Emirates ID for ${m.first_name ? `${m.first_name} ${m.last_name}` : `Member ${i + 1}`}`}
                  onResult={(result: ScanResult) => {
                    if (result.first_name) setMember(i, 'first_name', result.first_name)
                    if (result.last_name) setMember(i, 'last_name', result.last_name)
                    if (result.date_of_birth) setMember(i, 'date_of_birth', result.date_of_birth)
                    if (result.gender) {
                      const g = result.gender.toUpperCase()
                      setMember(i, 'gender', g === 'M' ? 'male' : g === 'F' ? 'female' : result.gender as Gender)
                    }
                    if (result.passport_number) setMember(i, 'passport_number', result.passport_number)
                    if (result.emirates_id) setMember(i, 'emirates_id', result.emirates_id)
                    if (result.document_expiry) setMember(i, 'document_expiry', result.document_expiry)
                    if (result.nationality) {
                      const match = NATIONALITIES.find(n => n.toLowerCase() === result.nationality!.toLowerCase())
                      if (match) setMember(i, 'nationality', match)
                    }
                  }}
                />
              </div>

              {/* UAE identity */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mt-4 mb-3">Identity Documents</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <SelectField label="Marital Status" value={m.marital_status}
                    onChange={v => setMember(i, 'marital_status', v)}
                    options={['single', 'married', 'divorced', 'widowed']} />
                  <div>
                    <label className="label">Emirates ID</label>
                    <input className="input" value={m.emirates_id} placeholder="784-YYYY-NNNNNNN-C"
                      onChange={e => setMember(i, 'emirates_id', e.target.value)}
                      onBlur={e => validateEid(i, e.target.value)} />
                    {eidErrors[i] && <p className="text-xs text-red-500 mt-1">{eidErrors[i]}</p>}
                  </div>
                  <div>
                    <label className="label">EID Expiry Date</label>
                    <input className="input" type="date" value={m.document_expiry}
                      onChange={e => setMember(i, 'document_expiry', e.target.value)} />
                  </div>
                  <Field label="Passport Number" value={m.passport_number}
                    onChange={v => setMember(i, 'passport_number', v)} />
                </div>
              </div>

              {/* Medical questionnaire */}
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Medical Questionnaire</p>
                <div className="border border-gray-200 rounded-xl overflow-hidden divide-y divide-gray-100">
                  {MEDICAL_QUESTIONS.map(q => {
                    const key = `q_${q.id === 'covid_positive' ? 'covid' : q.id === 'covid_complications' ? 'covid_complications' : q.id}` as keyof MemberRow
                    const val = m[key] as boolean
                    return (
                      <div key={q.id} className="px-4 py-3">
                        <YesNo label={q.label} value={val} onChange={v => setMember(i, key, v)} />
                        {(q as any).hasDetails && val && (
                          <textarea rows={3}
                            placeholder="Condition name, current medication, since when, treatment status…"
                            value={m.q_medical_details}
                            onChange={e => setMember(i, 'q_medical_details', e.target.value)}
                            className="input mt-2 resize-none" />
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Pregnancy (females only, if flag set) */}
              {form.any_pregnancy && m.gender === 'female' && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Pregnancy</p>
                  <div className="border border-gray-200 rounded-xl overflow-hidden px-4 py-3">
                    <YesNo label="Currently pregnant?" value={m.q_pregnant}
                      onChange={v => setMember(i, 'q_pregnant', v)} />
                    {m.q_pregnant && (
                      <div className="mt-3">
                        <label className="label">Weeks of pregnancy</label>
                        <input className="input" type="number" min={1} max={42}
                          value={m.q_pregnancy_weeks}
                          onChange={e => setMember(i, 'q_pregnancy_weeks', e.target.value)} />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Step 4: Finalize ──────────────────────────────────────────────────────────

function Step4({ form, onStepBack }: { form: WizardForm; onStepBack: () => void }) {
  const { toast } = useToast()
  const [remarks, setRemarks] = useState<RemarkItem[]>([])
  const [remarkText, setRemarkText] = useState('')
  const [addingRemark, setAddingRemark] = useState(false)
  const [uploadedDocs, setUploadedDocs] = useState<Record<string, UploadedDoc>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [loadingDoc, setLoadingDoc] = useState<string | null>(null)
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({})

  const appId = form.application_id

  const loadRemarks = () => {
    applicationsApi.listRemarks(appId)
      .then(r => setRemarks(r.data.data ?? []))
      .catch(() => {})
  }

  useEffect(() => { loadRemarks() }, [])

  const addRemark = async () => {
    if (!remarkText.trim()) return
    setAddingRemark(true)
    try {
      await applicationsApi.addRemark(appId, remarkText)
      setRemarkText('')
      loadRemarks()
      toast('Remark added.')
    } catch {
      toast('Failed to add remark.')
    } finally { setAddingRemark(false) }
  }

  const handleDownload = async (type: 'maf' | 'kyc' | 'tob') => {
    setLoadingDoc(type)
    try {
      const fn = type === 'maf' ? documentsApi.generateMaf : type === 'kyc' ? documentsApi.generateKyc : documentsApi.generateTob
      const res = await fn(appId)
      triggerDownload(res.data, `${type.toUpperCase()}-${form.application_number}.pdf`)
    } catch {
      toast(`Failed to generate ${type.toUpperCase()}.`)
    } finally { setLoadingDoc(null) }
  }

  const handlePreview = async (type: 'maf' | 'kyc' | 'tob') => {
    setLoadingDoc(`${type}-preview`)
    try {
      const fn = type === 'maf' ? documentsApi.generateMaf : type === 'kyc' ? documentsApi.generateKyc : documentsApi.generateTob
      const res = await fn(appId)
      const url = URL.createObjectURL(res.data)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 10000)
    } catch {
      toast(`Failed to preview ${type.toUpperCase()}.`)
    } finally { setLoadingDoc(null) }
  }

  const handleUpload = async (type: 'maf' | 'kyc' | 'tob', file: File) => {
    try {
      await documentsApi.uploadSigned(appId, file, type)
      setUploadedDocs(d => ({ ...d, [type]: { filename: file.name } }))
      toast(`${type.toUpperCase()} uploaded.`)
    } catch {
      toast(`Failed to upload ${type.toUpperCase()}.`)
    }
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await applicationsApi.submit(appId)
      setSubmitted(true)
      toast('Application submitted to underwriter.')
    } catch {
      toast('Failed to submit application.')
    } finally { setSubmitting(false) }
  }

  if (submitted) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Application Submitted</h2>
        <p className="text-gray-500 mb-1">Your application has been sent to the underwriter.</p>
        <p className="font-mono text-primary-700 font-semibold text-lg mb-6">{form.application_number}</p>
        <a href="/applications" className="btn-primary inline-flex items-center gap-2 px-6 py-2.5">
          View in Applications
        </a>
      </div>
    )
  }

  const docs: { type: 'maf' | 'kyc' | 'tob'; name: string }[] = [
    { type: 'maf', name: 'Medical Application Form (MAF)' },
    { type: 'kyc', name: 'KYC Form' },
    { type: 'tob', name: 'Table of Benefits (ToB)' },
  ]

  return (
    <div className="space-y-5">
      {/* Plan summary */}
      <div className="card p-4 flex items-center gap-4 bg-primary-50 border-primary-200">
        <div className="flex-1">
          <p className="text-xs text-primary-500 font-medium">Selected Plan</p>
          <p className="font-semibold text-primary-900">{form.plan_name}</p>
        </div>
        {form.quoted_total > 0 && (
          <div className="text-right">
            <p className="text-xs text-primary-400">Quoted Total</p>
            <p className="text-xl font-bold text-primary-700">
              AED {form.quoted_total.toLocaleString('en-AE', { minimumFractionDigits: 0 })}
            </p>
          </div>
        )}
        <button type="button" onClick={onStepBack}
          className="text-xs text-primary-600 hover:text-primary-800 underline flex-shrink-0">
          Edit Details
        </button>
      </div>

      {/* Documents */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-1">Application Documents</h3>
        <p className="text-xs text-gray-400 mb-4">Download, get signed, then upload the signed copies.</p>
        <div className="divide-y divide-gray-100">
          {docs.map(doc => (
            <div key={doc.type} className="py-3 flex flex-col sm:flex-row sm:items-center gap-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800">{doc.name}</p>
                {uploadedDocs[doc.type] && (
                  <p className="text-xs text-green-600 mt-0.5 flex items-center gap-1">
                    <Check className="w-3 h-3" /> {uploadedDocs[doc.type].filename}
                  </p>
                )}
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button type="button"
                  onClick={() => handleDownload(doc.type)}
                  disabled={loadingDoc === doc.type}
                  className="btn-secondary flex items-center gap-1.5 py-1.5 px-3 text-xs">
                  {loadingDoc === doc.type ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                  Download
                </button>
                <button type="button"
                  onClick={() => handlePreview(doc.type)}
                  disabled={loadingDoc === `${doc.type}-preview`}
                  className="btn-secondary flex items-center gap-1.5 py-1.5 px-3 text-xs">
                  {loadingDoc === `${doc.type}-preview` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
                  Preview
                </button>
                <label className="btn-secondary flex items-center gap-1.5 py-1.5 px-3 text-xs cursor-pointer">
                  <Upload className="w-3.5 h-3.5" /> Upload Signed
                  <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden"
                    ref={el => { fileRefs.current[doc.type] = el }}
                    onChange={e => {
                      const f = e.target.files?.[0]
                      if (f) handleUpload(doc.type, f)
                      e.target.value = ''
                    }} />
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Remarks */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <MessageSquare className="w-4 h-4 text-gray-400" /> Remarks
        </h3>
        {remarks.length > 0 && (
          <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
            {remarks.map((r, i) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-gray-700">{r.author_name}</span>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full capitalize">
                    {(r.author_role ?? '').replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs text-gray-400 ml-auto">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{r.text}</p>
              </div>
            ))}
          </div>
        )}
        {remarks.length === 0 && <p className="text-xs text-gray-400 italic mb-4">No remarks yet.</p>}
        <div className="flex gap-2">
          <textarea rows={2} value={remarkText} onChange={e => setRemarkText(e.target.value)}
            placeholder="Add a remark for the underwriter…"
            className="input flex-1 resize-none" />
          <button type="button" onClick={addRemark} disabled={addingRemark || !remarkText.trim()}
            className="btn-primary px-4 py-2 self-start text-sm disabled:opacity-50">
            {addingRemark ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Add'}
          </button>
        </div>
      </div>

      {/* Submit */}
      <button type="button" onClick={handleSubmit} disabled={submitting}
        className="btn-primary w-full py-3.5 flex items-center justify-center gap-2 text-base font-semibold">
        {submitting ? <><Loader2 className="w-5 h-5 animate-spin" /> Submitting…</> : 'Submit to Underwriter'}
      </button>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function NewPolicyPage() {
  const { toast } = useToast()
  const [step, setStep] = useState(1)
  const [form, setForm] = useState<WizardForm>(INITIAL_FORM)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  const principal = form.members[0]

  const validateStep1 = (): string | null => {
    if (!principal.first_name.trim()) return 'First name is required for the principal member.'
    if (!principal.last_name.trim()) return 'Last name is required for the principal member.'
    if (!principal.email.trim() || !principal.email.includes('@')) return 'Valid email is required for the principal member.'
    if (!principal.date_of_birth) return 'Date of birth is required for the principal member.'
    if (!principal.gender) return 'Gender is required for the principal member.'
    if (!principal.nationality) return 'Nationality is required for the principal member.'
    for (let i = 1; i < form.members.length; i++) {
      const m = form.members[i]
      if (!m.first_name.trim()) return `First name is required for family member ${i}.`
      if (!m.last_name.trim()) return `Last name is required for family member ${i}.`
      if (!m.date_of_birth) return `Date of birth is required for family member ${i}.`
    }
    return null
  }

  const validateStep3 = (): string | null => {
    for (const m of form.members) {
      if (m.emirates_id && !EID_PATTERN.test(m.emirates_id)) {
        return `Emirates ID format invalid for ${m.first_name}. Use: 784-YYYY-NNNNNNN-C`
      }
    }
    return null
  }

  const handleCreateApplication = async () => {
    const v3 = validateStep3()
    if (v3) { setError(v3); return }

    setCreating(true)
    setError('')
    try {
      const appRes = await applicationsApi.create({
        customer_email: principal.email,
        customer_name: `${principal.first_name} ${principal.last_name}`,
        plan_id: form.plan_id || undefined,
        product_id: form.product_id || undefined,
        member_count: form.members.length,
        sponsor_type: form.sponsor_type,
        trn: form.trn || undefined,
        existing_health_insurance: form.existing_policy,
        is_diplomatic_passport: form.is_diplomatic_passport,
        is_eid_under_process: form.is_eid_under_process,
        cover_amount: form.cover_amount ? Number(form.cover_amount) : undefined,
        co_payment_config: (form.copay_opt_pct || form.copay_pharmacy_pct || form.copay_lab_pct || form.copay_physio_pct) ? {
          opt_pct: Number(form.copay_opt_pct || 0),
          pharmacy_pct: Number(form.copay_pharmacy_pct || 0),
          lab_pct: Number(form.copay_lab_pct || 0),
          physio_pct: Number(form.copay_physio_pct || 0),
        } : undefined,
        additional_info: {
          insure_who: form.insure_who,
          policy_start_date: form.policy_start_date || undefined,
          any_medication: form.any_medication,
          any_pregnancy: form.any_pregnancy,
        },
      })

      const app = appRes.data.data
      const appId: string = app.id
      const appNumber: string = app.application_number

      for (const m of form.members) {
        const pregnancyQ = (form.any_pregnancy && m.gender === 'female' && m.q_pregnant)
          ? { is_pregnant: true, weeks: m.q_pregnancy_weeks ? Number(m.q_pregnancy_weeks) : undefined }
          : undefined

        await membersApi.add(appId, {
          first_name: m.first_name,
          last_name: m.last_name,
          date_of_birth: m.date_of_birth,
          relationship: m.relationship,
          gender: m.gender,
          email: m.email || undefined,
          phone: m.phone || undefined,
          nationality: m.nationality || undefined,
          height_cm: m.height_cm ? Number(m.height_cm) : undefined,
          weight_kg: m.weight_kg ? Number(m.weight_kg) : undefined,
          marital_status: m.marital_status || undefined,
          emirates_id: m.emirates_id || undefined,
          document_expiry: m.document_expiry || undefined,
          passport_number: m.passport_number || undefined,
          medical_questionnaire: buildMedicalQ(m),
          pregnancy_questionnaire: pregnancyQ,
        })
      }

      setForm(f => ({ ...f, application_id: appId, application_number: appNumber }))
      setStep(4)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string; errors?: { message: string }[] } } })
        ?.response?.data
      setError(msg?.errors?.[0]?.message ?? msg?.detail ?? 'Failed to create application. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  const handleNext = async () => {
    setError('')
    if (step === 1) {
      const v = validateStep1()
      if (v) { setError(v); return }
      setStep(2)
    } else if (step === 2) {
      if (!form.plan_id) { setError('Please select a plan.'); return }
      setStep(3)
    } else if (step === 3) {
      await handleCreateApplication()
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleBack = () => {
    setError('')
    if (step > 1) setStep(s => s - 1)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">New Policy</h1>
        <p className="text-sm text-gray-500 mt-1">Complete the 5-step wizard to submit an application to the underwriter.</p>
      </div>

      {/* Step indicator */}
      <div className="mb-6">
        <StepIndicator current={step} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-start gap-2.5 p-3.5 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />{error}
        </div>
      )}

      {/* Step content */}
      {step === 1 && <Step1 form={form} setForm={setForm} />}
      {step === 2 && (
        <Step2
          form={form}
          setForm={setForm}
          onPlanSelected={(planId, productId, planName, total) => {
            setForm(f => ({ ...f, plan_id: planId, product_id: productId, plan_name: planName, quoted_total: total }))
            setStep(3)
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
        />
      )}
      {step === 3 && <Step3 form={form} setForm={setForm} />}
      {step === 4 && <Step4 form={form} onStepBack={() => setStep(1)} />}

      {/* Navigation footer (steps 1-3 only) */}
      {step <= 3 && (
        <div className="flex items-center gap-3 mt-6 pt-4 border-t border-gray-200">
          {step > 1 && (
            <button type="button" onClick={handleBack} className="btn-secondary px-5 py-2.5">
              Back
            </button>
          )}
          <button type="button" onClick={handleNext} disabled={creating}
            className="btn-primary flex-1 py-2.5 flex items-center justify-center gap-2">
            {creating
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating application…</>
              : step === 3 ? 'Create Application & Continue' : 'Next'}
          </button>
        </div>
      )}
    </div>
  )
}
