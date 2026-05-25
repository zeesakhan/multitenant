import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  ShieldCheck, ArrowRight, ArrowLeft, CheckCircle, Upload,
  Users, CreditCard, AlertCircle, X, Plus,
  Loader2, Check, Lock, Smartphone, Building2, ChevronDown, ChevronUp,
  Camera, RotateCcw, Baby, Phone, Mail, FileText,
} from 'lucide-react'
import { adamjeeApi, UAEMemberInput } from '../../../services/adamjeeApi'

// ── Types ─────────────────────────────────────────────────────────────────────

interface Plan {
  id: string; name: string; code: string; base_premium: number
  description: string; coverages: Coverage[]; highlights: string[]
}
interface Coverage {
  id: string; name: string; coverage_type: string
  limit_amount: number | null; copay: number | null; description: string
}
interface Regulation { ref: string; title: string; summary: string }
interface Dependent {
  first_name: string; last_name: string; date_of_birth: string
  gender: 'M' | 'F'; relationship: 'spouse' | 'child' | 'infant' | 'parent' | 'sibling'
  nationality: string; passport_number: string; emirates_id: string
  document_expiry: string; visa_type: string
}
interface FormState {
  first_name: string; last_name: string; email: string; phone: string
  date_of_birth: string; gender: 'M' | 'F'; nationality: string
  document_type: 'passport' | 'emirates_id'; passport_number: string
  emirates_id: string; document_expiry: string; visa_type: string; place_of_birth: string
  selected_plan_id: string; dependents: Dependent[]
  pre_existing_conditions: boolean; pre_existing_details: string
  agreed_to_terms: boolean; agreed_to_regulations: boolean
  application_id: string; application_number: string; policy_number: string
  total_premium: number; payment_reference: string
}

const NATIONALITIES = [
  'UAE National','Pakistani','Indian','Filipino','Bangladeshi','Egyptian',
  'Jordanian','Saudi Arabian','British','American','Sri Lankan','Nepali',
  'Lebanese','Syrian','Yemeni','Ethiopian','Sudanese','Chinese','Other',
]
const VISA_TYPES = [
  'Employment Visa','Residence Visa (Family)','Investor Visa',
  'Student Visa','Retirement Visa','Green Visa','UAE National (No Visa)',
]

// step 0 = contact capture (pre-flow, no stepper)
// steps 1–6 = main flow
// step 7 = confirmation
const STEPS = [
  { num: 1, label: 'Details' }, { num: 2, label: 'Plan' },
  { num: 3, label: 'Family' }, { num: 4, label: 'Review' },
  { num: 5, label: 'Consent' }, { num: 6, label: 'Pay' },
]
const EMPTY_DEP: Dependent = {
  first_name:'',last_name:'',date_of_birth:'',gender:'M',
  relationship:'spouse',nationality:'',passport_number:'',
  emirates_id:'',document_expiry:'',visa_type:'',
}
const fmt = (n: number) => n.toLocaleString('en-AE',{minimumFractionDigits:2,maximumFractionDigits:2})

// ── Camera Capture Component ──────────────────────────────────────────────────

function CameraCapture({ onCapture, onClose }: { onCapture:(f:File)=>void; onClose:()=>void }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [stream, setStream] = useState<MediaStream|null>(null)
  const [capturedUrl, setCapturedUrl] = useState<string|null>(null)
  const [camError, setCamError] = useState('')
  const [camLoading, setCamLoading] = useState(true)

  useEffect(() => { startCamera(); return () => stopStream() }, [])

  const startCamera = async () => {
    setCamLoading(true); setCamError('')
    try {
      const s = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } },
      })
      setStream(s)
      if (videoRef.current) {
        videoRef.current.srcObject = s
        videoRef.current.onloadedmetadata = () => setCamLoading(false)
      }
    } catch (e: any) {
      setCamError(
        e?.name === 'NotAllowedError'
          ? 'Camera permission denied. Please allow camera access in your browser settings.'
          : 'Camera not available on this device. Please use the file upload option instead.'
      )
      setCamLoading(false)
    }
  }

  const stopStream = () => { stream?.getTracks().forEach(t => t.stop()) }

  const capture = () => {
    if (!videoRef.current || !canvasRef.current) return
    const { videoWidth: w, videoHeight: h } = videoRef.current
    canvasRef.current.width = w; canvasRef.current.height = h
    canvasRef.current.getContext('2d')?.drawImage(videoRef.current, 0, 0)
    setCapturedUrl(canvasRef.current.toDataURL('image/jpeg', 0.92))
  }

  const usePhoto = () => {
    if (!canvasRef.current || !capturedUrl) return
    canvasRef.current.toBlob(blob => {
      if (blob) onCapture(new File([blob], 'document.jpg', { type: 'image/jpeg' }))
    }, 'image/jpeg', 0.92)
    stopStream(); onClose()
  }

  const retake = () => setCapturedUrl(null)
  const handleClose = () => { stopStream(); onClose() }

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col" style={{ touchAction: 'none' }}>
      <div className="flex items-center justify-between px-4 py-3 bg-black/80 text-white flex-shrink-0">
        <div>
          <p className="font-semibold text-sm">Scan Document</p>
          <p className="text-xs text-white/60">Position your passport or Emirates ID within the frame</p>
        </div>
        <button onClick={handleClose} className="p-2 rounded-full bg-white/10 hover:bg-white/20">
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 relative overflow-hidden bg-black">
        {camLoading && !camError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-10 h-10 text-white animate-spin" />
            <p className="text-white/70 text-sm">Starting camera…</p>
          </div>
        )}
        {camError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-8 text-center">
            <Camera className="w-16 h-16 text-white/30" />
            <p className="text-white/80 text-sm leading-relaxed">{camError}</p>
            <button onClick={handleClose} className="px-5 py-2.5 bg-white/20 text-white rounded-xl text-sm font-semibold">
              Use File Upload Instead
            </button>
          </div>
        )}
        {!capturedUrl ? (
          <video ref={videoRef} autoPlay playsInline muted
            className="w-full h-full object-cover"
            style={{ display: camLoading || camError ? 'none' : 'block' }}
          />
        ) : (
          <img src={capturedUrl} alt="Captured document" className="w-full h-full object-contain" />
        )}
        {!capturedUrl && !camLoading && !camError && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="relative" style={{ width: '85%', aspectRatio: '1.586/1' }}>
              {[
                'top-0 left-0 border-t-4 border-l-4 rounded-tl-lg',
                'top-0 right-0 border-t-4 border-r-4 rounded-tr-lg',
                'bottom-0 left-0 border-b-4 border-l-4 rounded-bl-lg',
                'bottom-0 right-0 border-b-4 border-r-4 rounded-br-lg',
              ].map((cls, i) => (
                <div key={i} className={`absolute w-8 h-8 border-amber-400 ${cls}`} />
              ))}
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-white/60 text-xs bg-black/40 px-3 py-1.5 rounded-full">
                  Align document within frame
                </p>
              </div>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>
      <div className="flex-shrink-0 bg-black/90 px-6 py-6">
        {!capturedUrl ? (
          <div className="flex items-center justify-between max-w-xs mx-auto">
            <button onClick={handleClose} className="text-white/60 text-sm font-medium px-4 py-2">
              Cancel
            </button>
            <button
              onClick={capture}
              disabled={camLoading || !!camError}
              className="w-18 h-18 flex items-center justify-center disabled:opacity-30"
              aria-label="Capture photo"
            >
              <div className="w-16 h-16 rounded-full border-4 border-white flex items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-white" />
              </div>
            </button>
            <div className="w-16" />
          </div>
        ) : (
          <div className="flex gap-3 max-w-xs mx-auto">
            <button onClick={retake}
              className="flex-1 flex items-center justify-center gap-2 py-3 bg-white/20 text-white rounded-xl text-sm font-semibold">
              <RotateCcw className="w-4 h-4" /> Retake
            </button>
            <button onClick={usePhoto}
              className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold">
              <Check className="w-4 h-4" /> Use Photo
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Contact Capture Screen (step 0) ──────────────────────────────────────────

function ContactScreen({ contact, setContact, onNext, onBack, error, setError }: {
  contact: { email: string; phone: string }
  setContact: React.Dispatch<React.SetStateAction<{ email: string; phone: string }>>
  onNext: () => void
  onBack: () => void
  error: string
  setError: (e: string) => void
}) {
  const [termsOpen, setTermsOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-800 via-blue-700 to-blue-900 flex items-center justify-center px-4 py-10">
      {/* Terms Modal */}
      {termsOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center px-4"
          onClick={() => setTermsOpen(false)}
        >
          <div
            className="bg-white rounded-2xl p-6 max-w-sm w-full shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-gray-900 text-base">Contact Consent</h3>
              <button onClick={() => setTermsOpen(false)} className="p-1 rounded-lg hover:bg-gray-100">
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">
              We have your consent to reach out to you on the provided contacts.
            </p>
            <p className="text-xs text-gray-400 mt-3 leading-relaxed">
              By providing your email and mobile number, you consent to Adamjee Insurance contacting you
              regarding your insurance quote, application status, and policy updates. Your information is
              handled in accordance with UAE PDPL (Federal Decree-Law No. 45 of 2021).
            </p>
            <button
              onClick={() => setTermsOpen(false)}
              className="w-full mt-5 py-2.5 bg-blue-700 text-white rounded-xl text-sm font-semibold hover:bg-blue-800 transition-colors"
            >
              I Understand
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-7 sm:p-8">
        {/* Header */}
        <div className="text-center mb-7">
          <div className="w-14 h-14 bg-blue-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold text-gray-900">Get Your Coverage</h1>
          <p className="text-gray-500 text-sm mt-1.5 leading-relaxed">
            Enter your contact details to begin your application.
            <br />
            <span className="text-xs text-gray-400">We'll use these to follow up if you need help.</span>
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Email Address *</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="email"
                value={contact.email}
                onChange={e => { setContact(c => ({ ...c, email: e.target.value })); setError('') }}
                placeholder="your@email.com"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1.5">Mobile Number *</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              <input
                type="tel"
                value={contact.phone}
                onChange={e => { setContact(c => ({ ...c, phone: e.target.value })); setError('') }}
                placeholder="+971 5X XXX XXXX"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-400 mt-4 text-center">
          By clicking continue, you agree to our{' '}
          <button
            onClick={() => setTermsOpen(true)}
            className="text-blue-600 underline font-medium hover:text-blue-800 transition-colors"
          >
            contact terms
          </button>
        </p>

        <button
          onClick={onNext}
          className="w-full mt-4 flex items-center justify-center gap-2 py-3.5 bg-blue-700 text-white font-bold rounded-xl hover:bg-blue-800 transition-colors text-sm"
        >
          Agree Terms &amp; Continue <ArrowRight className="w-4 h-4" />
        </button>

        <button
          onClick={onBack}
          className="w-full mt-3 py-2.5 text-sm text-gray-500 hover:text-gray-700 text-center transition-colors"
        >
          ← Back to Plans
        </button>
      </div>
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AdamjeeBuyPage() {
  const navigate = useNavigate()
  // step 0 = contact capture; 1-6 = main flow; 7 = confirmation
  const [step, setStep] = useState(0)
  const [contact, setContact] = useState({ email: '', phone: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [plans, setPlans] = useState<Plan[]>([])
  const [regulations, setRegulations] = useState<Regulation[]>([])
  const [quote, setQuote] = useState<{ total_premium: number; breakdown: any[]; coverages: Coverage[] } | null>(null)
  const [expandedRegs, setExpandedRegs] = useState<Record<string,boolean>>({})
  const [expandedCoverages, setExpandedCoverages] = useState(false)
  const [ocrLoading, setOcrLoading] = useState(false)
  const [ocrMsg, setOcrMsg] = useState('')
  const [showCamera, setShowCamera] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const [form, setForm] = useState<FormState>({
    first_name:'',last_name:'',email:'',phone:'',date_of_birth:'',
    gender:'M',nationality:'',document_type:'passport',
    passport_number:'',emirates_id:'',document_expiry:'',visa_type:'',place_of_birth:'',
    selected_plan_id:'',dependents:[],
    pre_existing_conditions:false,pre_existing_details:'',
    agreed_to_terms:false,agreed_to_regulations:false,
    application_id:'',application_number:'',policy_number:'',
    total_premium:0,payment_reference:'',
  })
  const [card, setCard] = useState({
    number:'', expiry:'', cvv:'', name:'',
    method: 'card' as 'card' | 'apple_pay' | 'google_pay' | 'bank_transfer',
  })

  const set = (field: keyof FormState, value: unknown) =>
    setForm(f => ({ ...f, [field]: value }))

  useEffect(() => {
    adamjeeApi.getPlans()
      .then(r => setPlans((r.data.data ?? []).flatMap((p: any) => p.plans ?? [])))
      .catch(() => setError('Failed to load plans. Please try again.'))
    adamjeeApi.getRegulations()
      .then(r => setRegulations(r.data.data?.regulations ?? []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (!form.selected_plan_id || !form.first_name) return
    adamjeeApi.getQuote(form.selected_plan_id, buildMembers())
      .then(r => setQuote(r.data.data))
      .catch(() => {})
  }, [form.selected_plan_id, form.dependents, form.first_name])

  const buildMembers = (): UAEMemberInput[] => [
    {
      first_name: form.first_name, last_name: form.last_name,
      date_of_birth: form.date_of_birth, relationship: 'self', gender: form.gender,
      nationality: form.nationality || undefined,
      passport_number: form.document_type === 'passport' ? form.passport_number : undefined,
      emirates_id: form.document_type === 'emirates_id' ? form.emirates_id : undefined,
      document_expiry: form.document_expiry || undefined,
      visa_type: form.visa_type || undefined,
      place_of_birth: form.place_of_birth || undefined,
    },
    ...form.dependents.map(d => ({
      first_name: d.first_name, last_name: d.last_name,
      date_of_birth: d.date_of_birth,
      relationship: (d.relationship === 'infant' ? 'child' : d.relationship) as UAEMemberInput['relationship'],
      gender: d.gender,
      nationality: d.nationality || undefined,
      passport_number: d.passport_number || undefined,
      emirates_id: d.emirates_id || undefined,
      document_expiry: d.document_expiry || undefined,
      visa_type: d.visa_type || undefined,
    })),
  ]

  const handleOCR = async (file: File) => {
    setOcrLoading(true); setOcrMsg('')
    try {
      const res = await adamjeeApi.ocrDocument(file)
      const d = res.data.data
      if (d.first_name) set('first_name', d.first_name)
      if (d.last_name) set('last_name', d.last_name)
      if (d.date_of_birth) set('date_of_birth', d.date_of_birth)
      if (d.nationality) set('nationality', d.nationality)
      if (d.gender) set('gender', d.gender)
      if (d.passport_number) { set('passport_number', d.passport_number); set('document_type', 'passport') }
      if (d.emirates_id) { set('emirates_id', d.emirates_id); set('document_type', 'emirates_id') }
      if (d.document_expiry) set('document_expiry', d.document_expiry)
      if (d.place_of_birth) set('place_of_birth', d.place_of_birth)
      setOcrMsg(res.data.message || 'Scanned! Please verify the details below.')
    } catch {
      setOcrMsg('Could not auto-read document. Please fill in your details manually.')
    } finally {
      setOcrLoading(false)
    }
  }

  const updDep = (i: number, f: keyof Dependent, v: string) => {
    const deps = [...form.dependents]; deps[i] = { ...deps[i], [f]: v }; set('dependents', deps)
  }

  const selectedPlan = plans.find(p => p.id === form.selected_plan_id)

  const validate = () => {
    setError('')
    if (step === 1) {
      if (!form.first_name || !form.last_name) return 'First and last name are required.'
      if (!form.date_of_birth) return 'Date of birth is required.'
      if (!form.nationality) return 'Nationality is required.'
      if (form.document_type === 'passport' && !form.passport_number) return 'Passport number is required.'
      if (form.document_type === 'emirates_id' && !form.emirates_id) return 'Emirates ID is required.'
      if (!form.document_expiry) return 'Document expiry date is required.'
    }
    if (step === 2 && !form.selected_plan_id) return 'Please select a plan.'
    if (step === 5) {
      if (!form.agreed_to_terms) return 'You must agree to the Terms & Conditions.'
      if (!form.agreed_to_regulations) return 'You must agree to UAE Insurance Regulations.'
    }
    if (step === 6 && card.method === 'card') {
      if (card.number.replace(/\s/g,'').length < 16) return 'Valid 16-digit card number required.'
      if (!card.expiry.match(/^\d{2}\/\d{2}$/)) return 'Card expiry must be MM/YY.'
      if (card.cvv.length < 3) return 'Valid CVV required.'
      if (!card.name) return 'Cardholder name is required.'
    }
    return null
  }

  const next = async () => {
    const err = validate(); if (err) { setError(err); return }
    if (step === 5) { await submitApplication(); return }
    if (step === 6) { await submitPayment(); return }
    setStep(s => s + 1); setError(''); window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const submitApplication = async () => {
    setLoading(true); setError('')
    try {
      const res = await adamjeeApi.apply({
        plan_id: form.selected_plan_id, members: buildMembers(),
        email: form.email, phone: form.phone,
        pre_existing_conditions: form.pre_existing_conditions,
        pre_existing_details: form.pre_existing_details || undefined,
        agreed_to_terms: form.agreed_to_terms,
        agreed_to_regulations: form.agreed_to_regulations,
      })
      const d = res.data.data
      set('application_id', d.application_id)
      set('application_number', d.application_number)
      set('total_premium', d.total_premium)
      setStep(6); window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to submit application. Please try again.')
    } finally { setLoading(false) }
  }

  const submitPayment = async () => {
    setLoading(true); setError('')
    try {
      const last4 = card.number.replace(/\s/g,'').slice(-4)
      const brand = card.number.startsWith('4') ? 'Visa' : card.number.startsWith('5') ? 'Mastercard' : card.number.startsWith('3') ? 'Amex' : 'Card'
      const res = await adamjeeApi.pay(form.application_id, {
        method: card.method,
        card_last4: card.method === 'card' ? last4 : undefined,
        card_brand: card.method === 'card' ? brand : undefined,
        cardholder_name: card.name || undefined,
      })
      const d = res.data.data
      set('policy_number', d.policy_number)
      set('payment_reference', d.reference)
      setStep(7); window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Payment failed. Please try again.')
    } finally { setLoading(false) }
  }

  // ── Step 0: Contact Capture ─────────────────────────────────────────────────
  if (step === 0) {
    return (
      <ContactScreen
        contact={contact}
        setContact={setContact}
        onNext={() => {
          if (!contact.email.includes('@')) { setError('Valid email address is required.'); return }
          if (!contact.phone.trim()) { setError('Mobile number is required.'); return }
          set('email', contact.email)
          set('phone', contact.phone)
          setError('')
          setStep(1)
          window.scrollTo({ top: 0, behavior: 'smooth' })
        }}
        onBack={() => navigate('/buy/adamjee')}
        error={error}
        setError={setError}
      />
    )
  }

  // ── Step 7: Confirmation ────────────────────────────────────────────────────
  if (step === 7) return (
    <Confirmation
      policyNumber={form.policy_number} applicationNumber={form.application_number}
      paymentReference={form.payment_reference} totalPremium={form.total_premium}
      planName={selectedPlan?.name || ''} email={form.email}
      onDone={() => navigate('/buy/adamjee')}
    />
  )

  // ── Steps 1–6 ───────────────────────────────────────────────────────────────
  return (
    <>
      {showCamera && (
        <CameraCapture
          onCapture={file => { setShowCamera(false); handleOCR(file) }}
          onClose={() => setShowCamera(false)}
        />
      )}

      <div className="min-h-screen bg-gray-50 pb-28 sm:pb-0">
        {/* Nav */}
        <nav className="sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-13">
            <Link to="/buy/adamjee" className="flex items-center gap-2 py-3">
              <div className="w-7 h-7 rounded-lg bg-blue-700 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-blue-800 text-sm hidden xs:block">Adamjee Insurance</span>
              <span className="font-bold text-blue-800 text-sm xs:hidden">Adamjee</span>
            </Link>
            <span className="text-xs text-gray-400 hidden sm:block">UAE Health Insurance · DHA Compliant</span>
            <span className="text-xs text-gray-400 sm:hidden">DHA Compliant</span>
          </div>
        </nav>

        {/* Step indicator */}
        <div className="bg-white border-b border-gray-100 overflow-x-auto">
          <div className="max-w-5xl mx-auto px-3 py-2.5">
            <div className="flex items-center gap-1 min-w-max mx-auto">
              {STEPS.map((s, i) => (
                <div key={s.num} className="flex items-center gap-0.5 sm:gap-1">
                  <div className={`flex items-center gap-1 px-2 sm:px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-colors ${
                    step === s.num ? 'bg-blue-700 text-white' :
                    step > s.num  ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-400'
                  }`}>
                    {step > s.num ? <Check className="w-3 h-3" /> : <span className="w-3 text-center">{s.num}</span>}
                    <span>{s.label}</span>
                  </div>
                  {i < STEPS.length - 1 && <div className="w-2 sm:w-3 h-px bg-gray-200 flex-shrink-0" />}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />{error}
            </div>
          )}

          {/* ── Step 1: Document Upload + Personal Details ─────────────────── */}
          {step === 1 && (
            <Card title="Your Details" subtitle="Scan your passport or Emirates ID to auto-fill — then verify and complete the form below.">

              {/* Document Upload — at top */}
              <div className="mb-5">
                <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Identity Document</p>

                {/* Doc type toggle */}
                <div className="flex gap-2 mb-4">
                  {(['passport', 'emirates_id'] as const).map(dt => (
                    <button key={dt} type="button" onClick={() => set('document_type', dt)}
                      className={`flex-1 py-3 px-3 rounded-xl border-2 text-sm font-semibold transition-colors touch-manipulation ${
                        form.document_type === dt ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-600'
                      }`}>
                      {dt === 'passport' ? '🛂 Passport' : '🪪 Emirates ID'}
                    </button>
                  ))}
                </div>

                {/* Upload options */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <button type="button" onClick={() => setShowCamera(true)}
                    className="flex flex-col items-center gap-2 p-4 sm:p-5 border-2 border-blue-300 bg-blue-50 rounded-2xl hover:bg-blue-100 active:bg-blue-200 transition-colors touch-manipulation">
                    <Camera className="w-7 h-7 text-blue-600" />
                    <span className="text-sm font-semibold text-blue-700">Take Photo</span>
                    <span className="text-xs text-blue-500 text-center">Use your camera</span>
                  </button>
                  <button type="button" onClick={() => fileRef.current?.click()}
                    className="flex flex-col items-center gap-2 p-4 sm:p-5 border-2 border-gray-200 bg-white rounded-2xl hover:bg-gray-50 active:bg-gray-100 transition-colors touch-manipulation">
                    <Upload className="w-7 h-7 text-gray-500" />
                    <span className="text-sm font-semibold text-gray-700">Upload File</span>
                    <span className="text-xs text-gray-400 text-center">JPEG, PNG, PDF</span>
                  </button>
                </div>
                <input ref={fileRef} type="file" accept="image/*,application/pdf" className="hidden"
                  onChange={e => { const f = e.target.files?.[0]; if (f) handleOCR(f); e.target.value = '' }} />

                {/* OCR status */}
                {ocrLoading && (
                  <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl mb-3 text-sm text-blue-700">
                    <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" /> Scanning document…
                  </div>
                )}
                {ocrMsg && !ocrLoading && (
                  <div className={`flex items-start gap-2.5 p-3.5 rounded-xl mb-3 text-sm ${
                    ocrMsg.includes('Could not')
                      ? 'bg-amber-50 border border-amber-200 text-amber-700'
                      : 'bg-green-50 border border-green-200 text-green-700'
                  }`}>
                    {ocrMsg.includes('Could not')
                      ? <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0"/>
                      : <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0"/>}
                    {ocrMsg}
                  </div>
                )}

                {/* Document number fields */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {form.document_type === 'passport'
                    ? <Field label="Passport Number *" value={form.passport_number} onChange={v => set('passport_number', v)} placeholder="e.g. A12345678" />
                    : <Field label="Emirates ID *" value={form.emirates_id} onChange={v => set('emirates_id', v)} placeholder="784-XXXX-XXXXXXX-X" />}
                  <Field label="Document Expiry *" value={form.document_expiry} onChange={v => set('document_expiry', v)} type="date" />
                </div>

                <div className="mt-3 flex items-start gap-2 p-3 bg-blue-50 rounded-xl text-xs text-blue-700">
                  <Lock className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                  Data encrypted per UAE PDPL (Federal Decree-Law No. 45 of 2021). Document images are not stored.
                </div>
              </div>

              {/* Divider */}
              <div className="border-t border-gray-100 my-5" />

              {/* Personal Details — auto-populated by OCR */}
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Personal Details — verify or complete manually</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="First Name *" value={form.first_name} onChange={v => set('first_name', v)} placeholder="As on passport/ID" />
                <Field label="Last Name *" value={form.last_name} onChange={v => set('last_name', v)} placeholder="As on passport/ID" />
                <Field label="Date of Birth *" value={form.date_of_birth} onChange={v => set('date_of_birth', v)} type="date" />
                <div>
                  <label className="block text-xs font-semibold text-gray-600 mb-1.5">Gender *</label>
                  <div className="flex gap-2">
                    {(['M', 'F'] as const).map(g => (
                      <button key={g} type="button" onClick={() => set('gender', g)}
                        className={`flex-1 py-2.5 rounded-xl border text-sm font-semibold transition-colors touch-manipulation ${
                          form.gender === g ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-300 text-gray-600'
                        }`}>
                        {g === 'M' ? '♂ Male' : '♀ Female'}
                      </button>
                    ))}
                  </div>
                </div>
                <SelectField label="Nationality *" value={form.nationality} onChange={v => set('nationality', v)} options={NATIONALITIES} placeholder="Select nationality" />
                <SelectField label="Visa Type" value={form.visa_type} onChange={v => set('visa_type', v)} options={VISA_TYPES} placeholder="Select visa type" />
                <div className="sm:col-span-2">
                  <Field label="Place of Birth" value={form.place_of_birth} onChange={v => set('place_of_birth', v)} placeholder="City, Country" />
                </div>
              </div>
            </Card>
          )}

          {/* ── Step 2: Plan Selection ──────────────────────────────────────── */}
          {step === 2 && (
            <Card title="Select Your Plan" subtitle="All plans are DHA Compliant · AED 1,000,000 annual limit · TPA: MEDNET">
              {plans.length === 0 ? (
                <div className="text-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-400 mx-auto mb-3"/>
                  <p className="text-gray-400 text-sm">Loading plans…</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {plans.map(plan => {
                    const sel = form.selected_plan_id === plan.id
                    return (
                      <div key={plan.id} onClick={() => set('selected_plan_id', plan.id)}
                        className={`border-2 rounded-2xl p-4 sm:p-5 cursor-pointer transition-all touch-manipulation ${
                          sel ? 'border-blue-600 bg-blue-50 shadow-md' : 'border-gray-200 bg-white hover:border-blue-300'
                        }`}>
                        <div className="flex items-start gap-3">
                          <div className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                            sel ? 'border-blue-600 bg-blue-600' : 'border-gray-300'
                          }`}>
                            {sel && <Check className="w-3 h-3 text-white"/>}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-4">
                              <h3 className="font-bold text-gray-900 text-base">{plan.name}</h3>
                              <div className="text-left sm:text-right flex-shrink-0">
                                <span className="text-xl sm:text-2xl font-extrabold text-blue-800">AED {fmt(plan.base_premium)}</span>
                                <span className="text-xs text-gray-400">/year</span>
                                <p className="text-xs text-gray-400">≈ AED {fmt(plan.base_premium / 12)}/mo</p>
                              </div>
                            </div>
                            <p className="text-xs text-gray-500 mt-1 mb-2 leading-relaxed">{plan.description}</p>
                            <div className="flex flex-wrap gap-1.5">
                              {plan.highlights.slice(0, 3).map(h => (
                                <span key={h} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{h}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                        {sel && (
                          <div className="mt-3 pt-3 border-t border-blue-200 ml-8">
                            <button type="button" onClick={e => { e.stopPropagation(); setExpandedCoverages(v => !v) }}
                              className="flex items-center gap-1 text-xs text-blue-600 font-semibold mb-2">
                              {expandedCoverages ? <ChevronUp className="w-3.5 h-3.5"/> : <ChevronDown className="w-3.5 h-3.5"/>}
                              {expandedCoverages ? 'Hide' : 'Show all'} {plan.coverages.length} coverages
                            </button>
                            {expandedCoverages && (
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                                {plan.coverages.map(c => (
                                  <div key={c.id} className="flex items-start gap-1.5 text-xs text-gray-600">
                                    <CheckCircle className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0"/>
                                    <span><strong>{c.name}</strong>
                                      {c.limit_amount ? ` — AED ${fmt(c.limit_amount)}` : ''}
                                      {c.copay !== null ? ` · ${c.copay}% co-pay` : ''}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </Card>
          )}

          {/* ── Step 3: Family Members ──────────────────────────────────────── */}
          {step === 3 && (
            <Card title="Add Family Members" subtitle="Cover your spouse, children, infants, or parents under the same policy at discounted rates.">
              {form.dependents.length === 0 && (
                <div className="text-center py-8 border-2 border-dashed border-gray-200 rounded-2xl mb-4">
                  <Users className="w-10 h-10 text-gray-200 mx-auto mb-2"/>
                  <p className="text-gray-500 text-sm font-medium">No dependents added yet</p>
                  <p className="text-xs text-gray-400 mt-1">Spouse: 80% · Child/Infant: 40% · Parent: 75% of base premium</p>
                </div>
              )}
              {form.dependents.map((dep, idx) => (
                <div key={idx} className="border border-gray-200 rounded-2xl p-4 mb-3 bg-white">
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-semibold text-gray-800 text-sm capitalize">
                      {dep.relationship === 'infant' ? '👶 Infant' : dep.relationship || 'Dependent'} {idx + 1}
                      {dep.first_name && <span className="text-gray-400 font-normal"> — {dep.first_name}</span>}
                    </p>
                    <button type="button" onClick={() => set('dependents', form.dependents.filter((_, i) => i !== idx))}
                      className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50">
                      <X className="w-4 h-4"/>
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <Field label="First Name *" value={dep.first_name} onChange={v => updDep(idx, 'first_name', v)}/>
                    <Field label="Last Name *" value={dep.last_name} onChange={v => updDep(idx, 'last_name', v)}/>
                    <Field label="Date of Birth *" value={dep.date_of_birth} onChange={v => updDep(idx, 'date_of_birth', v)} type="date"/>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1.5">Relationship *</label>
                      <select value={dep.relationship} onChange={e => updDep(idx, 'relationship', e.target.value)}
                        className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option value="spouse">Spouse</option>
                        <option value="child">Child</option>
                        <option value="infant">Infant (under 1 year)</option>
                        <option value="parent">Parent</option>
                        <option value="sibling">Sibling</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1.5">Gender *</label>
                      <div className="flex gap-2">
                        {(['M', 'F'] as const).map(g => (
                          <button key={g} type="button" onClick={() => updDep(idx, 'gender', g)}
                            className={`flex-1 py-2 rounded-xl border text-sm font-semibold touch-manipulation ${
                              dep.gender === g ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-300 text-gray-600'
                            }`}>{g === 'M' ? '♂ M' : '♀ F'}</button>
                        ))}
                      </div>
                    </div>
                    <SelectField label="Nationality" value={dep.nationality} onChange={v => updDep(idx, 'nationality', v)} options={NATIONALITIES} placeholder="Select"/>
                    {dep.relationship !== 'infant' && (
                      <>
                        <Field label="Passport / EID Number" value={dep.passport_number || dep.emirates_id} onChange={v => updDep(idx, 'passport_number', v)} placeholder="Document number"/>
                        <Field label="Document Expiry" value={dep.document_expiry} onChange={v => updDep(idx, 'document_expiry', v)} type="date"/>
                      </>
                    )}
                    {dep.relationship === 'infant' && (
                      <div className="sm:col-span-2">
                        <div className="p-2.5 bg-blue-50 rounded-xl text-xs text-blue-700 flex items-center gap-2">
                          <Baby className="w-3.5 h-3.5 flex-shrink-0"/>
                          Document details are optional for infants. Birth certificate can be submitted later.
                        </div>
                      </div>
                    )}
                  </div>
                  {selectedPlan && dep.first_name && (
                    <div className="mt-3 p-2.5 bg-blue-50 rounded-lg text-xs text-blue-700">
                      Estimated: AED {fmt(selectedPlan.base_premium * (
                        dep.relationship === 'spouse' ? 0.80 :
                        dep.relationship === 'child' ? 0.40 :
                        dep.relationship === 'infant' ? 0.40 :
                        dep.relationship === 'parent' ? 0.75 : 0.65
                      ))}/yr
                    </div>
                  )}
                </div>
              ))}

              {/* Quick-add buttons */}
              <div className="flex flex-wrap gap-2">
                {([
                  { rel: 'spouse', label: 'Spouse', icon: <Plus className="w-4 h-4"/> },
                  { rel: 'child', label: 'Child', icon: <Plus className="w-4 h-4"/> },
                  { rel: 'infant', label: 'Infant', icon: <Baby className="w-4 h-4"/> },
                  { rel: 'parent', label: 'Parent', icon: <Plus className="w-4 h-4"/> },
                  { rel: 'sibling', label: 'Sibling', icon: <Plus className="w-4 h-4"/> },
                ] as const).map(({ rel, label, icon }) => (
                  <button key={rel} type="button"
                    onClick={() => set('dependents', [...form.dependents, { ...EMPTY_DEP, relationship: rel }])}
                    className={`flex items-center gap-1.5 px-4 py-2.5 border-2 border-dashed rounded-xl text-sm font-semibold hover:bg-blue-50 touch-manipulation ${
                      rel === 'infant'
                        ? 'border-amber-300 text-amber-700 hover:bg-amber-50'
                        : 'border-blue-300 text-blue-700'
                    }`}>
                    {icon} {label}
                  </button>
                ))}
              </div>

              {quote && (
                <div className="mt-5 p-4 bg-blue-700 rounded-2xl text-white">
                  <p className="text-blue-200 text-xs mb-1">Total for {1 + form.dependents.length} member(s)</p>
                  <p className="text-3xl font-extrabold">AED {fmt(quote.total_premium)}</p>
                  <p className="text-blue-300 text-xs mt-1">≈ AED {fmt(quote.total_premium / 12)}/month</p>
                </div>
              )}
            </Card>
          )}

          {/* ── Step 4: Review ──────────────────────────────────────────────── */}
          {step === 4 && (
            <Card title="Review Your Application" subtitle="Please verify all details before proceeding.">
              <ReviewSection title="Primary Insured">
                <RR label="Name" value={`${form.first_name} ${form.last_name}`}/>
                <RR label="Date of Birth" value={form.date_of_birth}/>
                <RR label="Gender" value={form.gender === 'M' ? 'Male' : 'Female'}/>
                <RR label="Nationality" value={form.nationality}/>
                <RR label="ID" value={form.document_type === 'passport' ? `Passport: ${form.passport_number}` : `Emirates ID: ${form.emirates_id}`}/>
                <RR label="Expiry" value={form.document_expiry}/>
                {form.visa_type && <RR label="Visa" value={form.visa_type}/>}
                <RR label="Email" value={form.email}/>
                <RR label="Phone" value={form.phone}/>
              </ReviewSection>
              {form.dependents.length > 0 && (
                <ReviewSection title={`Dependents (${form.dependents.length})`}>
                  {form.dependents.map((d, i) => (
                    <div key={i} className="py-2 border-b border-gray-100 last:border-0">
                      <p className="text-sm font-medium text-gray-800">
                        {d.first_name} {d.last_name}{' '}
                        <span className="text-gray-400 text-xs capitalize">
                          ({d.relationship === 'infant' ? 'infant' : d.relationship})
                        </span>
                      </p>
                      <p className="text-xs text-gray-500">DOB: {d.date_of_birth} · {d.gender === 'M' ? 'Male' : 'Female'}</p>
                    </div>
                  ))}
                </ReviewSection>
              )}
              <ReviewSection title="Selected Plan">
                <RR label="Plan" value={selectedPlan?.name || ''}/>
                <RR label="TPA" value="MEDNET"/>
                <RR label="Annual Limit" value="AED 1,000,000 / person"/>
                <RR label="Compliance" value="DHA Compliant"/>
              </ReviewSection>
              {quote && (
                <div className="bg-blue-700 rounded-2xl p-4 sm:p-5 text-white">
                  <p className="font-bold text-base mb-3">Premium Summary</p>
                  {quote.breakdown.map((b: any, i: number) => (
                    <div key={i} className="flex justify-between text-sm py-1.5 border-b border-blue-600">
                      <span className="text-blue-200 capitalize">{b.relationship} — {b.first_name}</span>
                      <span className="font-semibold">AED {fmt(b.premium)}</span>
                    </div>
                  ))}
                  <div className="flex justify-between mt-3 pt-2">
                    <span className="font-bold text-blue-100">Total Annual</span>
                    <span className="font-extrabold text-xl">AED {fmt(quote.total_premium)}</span>
                  </div>
                  <p className="text-blue-300 text-xs mt-1 text-right">≈ AED {fmt(quote.total_premium / 12)}/month</p>
                </div>
              )}
            </Card>
          )}

          {/* ── Step 5: Consent ─────────────────────────────────────────────── */}
          {step === 5 && (
            <Card title="UAE Regulatory Compliance" subtitle="Read the applicable laws and provide your mandatory consents before proceeding.">
              <div className="space-y-2 mb-5">
                {regulations.map(reg => (
                  <div key={reg.ref} className="border border-gray-200 rounded-xl overflow-hidden">
                    <button type="button" onClick={() => setExpandedRegs(p => ({ ...p, [reg.ref]: !p[reg.ref] }))}
                      className="w-full flex items-center justify-between p-3.5 bg-gray-50 hover:bg-gray-100 text-left touch-manipulation">
                      <div>
                        <p className="text-xs font-bold text-blue-700">{reg.ref}</p>
                        <p className="text-sm font-semibold text-gray-800">{reg.title}</p>
                      </div>
                      {expandedRegs[reg.ref]
                        ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0"/>
                        : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0"/>}
                    </button>
                    {expandedRegs[reg.ref] && (
                      <div className="p-4 text-sm text-gray-600 leading-relaxed border-t border-gray-200">{reg.summary}</div>
                    )}
                  </div>
                ))}
              </div>

              <div className="border border-amber-200 rounded-xl p-4 bg-amber-50 mb-4">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input type="checkbox" checked={form.pre_existing_conditions}
                    onChange={e => set('pre_existing_conditions', e.target.checked)}
                    className="mt-1 w-4 h-4 text-blue-600 rounded flex-shrink-0"/>
                  <div>
                    <p className="text-sm font-semibold text-amber-800">Pre-existing Conditions Declaration</p>
                    <p className="text-xs text-amber-700 mt-1">I or a listed dependent has pre-existing or chronic conditions. (All declared conditions covered — AED 150,000 sub-limit.)</p>
                  </div>
                </label>
                {form.pre_existing_conditions && (
                  <textarea rows={3} placeholder="Please describe the condition(s)…"
                    value={form.pre_existing_details} onChange={e => set('pre_existing_details', e.target.value)}
                    className="mt-3 w-full border border-amber-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"/>
                )}
              </div>

              <div className="space-y-3">
                <Consent checked={form.agreed_to_regulations} onChange={v => set('agreed_to_regulations', v)}
                  label="I have read and agree to the UAE Insurance Regulations summarised above, including Dubai Health Insurance Law No. 11 of 2013 and all applicable federal laws."/>
                <Consent checked={form.agreed_to_terms} onChange={v => set('agreed_to_terms', v)}
                  label="I agree to Adamjee Insurance Terms & Conditions and Privacy Policy. I consent to collection and processing of my personal data per UAE PDPL."/>
                <Consent checked readOnly
                  label="I declare all information provided is true and accurate. I understand misrepresentation may result in policy cancellation and is a criminal offence under UAE law."/>
              </div>
            </Card>
          )}

          {/* ── Step 6: Payment ─────────────────────────────────────────────── */}
          {step === 6 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
              {/* Order summary */}
              <div className="lg:col-span-1 lg:order-2 order-1">
                <div className="bg-blue-800 rounded-2xl p-4 sm:p-5 text-white lg:sticky lg:top-20">
                  <p className="font-bold text-base mb-4">Order Summary</p>
                  <div className="space-y-3 mb-4 text-sm">
                    <div><p className="text-blue-300 text-xs">Plan</p><p className="font-semibold">{selectedPlan?.name}</p></div>
                    <div><p className="text-blue-300 text-xs">Application</p><p className="font-mono text-xs">{form.application_number}</p></div>
                    <div><p className="text-blue-300 text-xs">Members</p><p className="font-semibold">{1 + form.dependents.length} person(s)</p></div>
                  </div>
                  {quote && (
                    <>
                      <div className="border-t border-blue-700 pt-3 space-y-1">
                        {quote.breakdown.map((b: any, i: number) => (
                          <div key={i} className="flex justify-between text-xs">
                            <span className="text-blue-300 capitalize">{b.first_name} ({b.relationship})</span>
                            <span>AED {fmt(b.premium)}</span>
                          </div>
                        ))}
                      </div>
                      <div className="border-t border-blue-700 mt-3 pt-3 flex justify-between items-end">
                        <span className="font-bold text-sm">Total / Year</span>
                        <div className="text-right">
                          <p className="font-extrabold text-xl">AED {fmt(quote.total_premium)}</p>
                          <p className="text-blue-300 text-xs">≈ AED {fmt(quote.total_premium / 12)}/mo</p>
                        </div>
                      </div>
                    </>
                  )}
                  <div className="mt-3 p-2.5 bg-blue-700/50 rounded-xl text-xs text-blue-200 flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5 flex-shrink-0"/> Instant policy after payment
                  </div>
                </div>
              </div>

              {/* Payment form */}
              <div className="lg:col-span-2 lg:order-1 order-2">
                <Card title="Secure Payment" subtitle="All transactions are 256-bit SSL encrypted. PCI DSS Level 1 compliant.">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
                    {[
                      { key: 'card', label: 'Card', icon: <CreditCard className="w-4 h-4"/> },
                      { key: 'apple_pay', label: 'Apple Pay', icon: <Smartphone className="w-4 h-4"/> },
                      { key: 'google_pay', label: 'Google Pay', icon: <Smartphone className="w-4 h-4"/> },
                      { key: 'bank_transfer', label: 'Bank Transfer', icon: <Building2 className="w-4 h-4"/> },
                    ].map(({ key, label, icon }) => (
                      <button key={key} type="button"
                        onClick={() => setCard(c => ({ ...c, method: key as typeof card.method }))}
                        className={`flex flex-col items-center gap-1 p-2.5 sm:p-3 rounded-xl border-2 text-xs font-semibold transition-all touch-manipulation ${
                          card.method === key ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 text-gray-500 hover:border-blue-200'
                        }`}>
                        {icon}{label}
                      </button>
                    ))}
                  </div>

                  {card.method === 'card' && (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-gray-600 mb-1.5">Card Number *</label>
                        <div className="relative">
                          <input type="tel" inputMode="numeric" maxLength={19}
                            value={card.number}
                            onChange={e => {
                              const v = e.target.value.replace(/\D/g, '').slice(0, 16)
                              setCard(c => ({ ...c, number: v.replace(/(.{4})/g, '$1 ').trim() }))
                            }}
                            className="w-full px-3 sm:px-4 py-3 border border-gray-300 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 pr-20"
                            placeholder="1234 5678 9012 3456"/>
                          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
                            {['VISA','MC'].map(b => <span key={b} className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded font-bold">{b}</span>)}
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-semibold text-gray-600 mb-1.5">Expiry (MM/YY) *</label>
                          <input type="tel" inputMode="numeric" maxLength={5} value={card.expiry}
                            onChange={e => { let v = e.target.value.replace(/\D/g,''); if (v.length >= 2) v = v.slice(0,2) + '/' + v.slice(2,4); setCard(c => ({ ...c, expiry: v })) }}
                            className="w-full px-3 py-3 border border-gray-300 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="MM/YY"/>
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-600 mb-1.5">CVV *</label>
                          <input type="password" inputMode="numeric" maxLength={4} value={card.cvv}
                            onChange={e => setCard(c => ({ ...c, cvv: e.target.value.replace(/\D/g,'') }))}
                            className="w-full px-3 py-3 border border-gray-300 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="•••"/>
                        </div>
                      </div>
                      <Field label="Cardholder Name *" value={card.name} onChange={v => setCard(c => ({ ...c, name: v }))} placeholder="As on card"/>
                    </div>
                  )}

                  {card.method === 'apple_pay' && (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-black rounded-2xl flex items-center justify-center mx-auto mb-3">
                        <Smartphone className="w-8 h-8 text-white"/>
                      </div>
                      <p className="font-semibold text-gray-800 mb-1">Apple Pay</p>
                      <p className="text-sm text-gray-500">Tap "Pay Now" to complete with Apple Pay.</p>
                    </div>
                  )}
                  {card.method === 'google_pay' && (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-white border-2 border-gray-200 rounded-2xl flex items-center justify-center mx-auto mb-3">
                        <span className="text-2xl font-bold text-blue-600">G</span>
                      </div>
                      <p className="font-semibold text-gray-800 mb-1">Google Pay</p>
                      <p className="text-sm text-gray-500">Tap "Pay Now" to complete with Google Pay.</p>
                    </div>
                  )}
                  {card.method === 'bank_transfer' && (
                    <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-2.5 text-sm">
                      <p className="font-semibold text-gray-800">Bank Transfer Details</p>
                      {[
                        ['Bank', 'Emirates NBD'],
                        ['Account Name', 'Adamjee Insurance LLC'],
                        ['IBAN', 'AE070331234567890123456'],
                        ['Reference', form.application_number],
                      ].map(([l, v]) => (
                        <div key={l} className="flex flex-col sm:flex-row sm:justify-between gap-0.5 sm:gap-4">
                          <span className="text-gray-500 text-xs">{l}</span>
                          <span className="font-mono text-xs font-medium">{v}</span>
                        </div>
                      ))}
                      <div className="p-2.5 bg-amber-50 rounded-lg text-xs text-amber-700">
                        Policy issued within 1 business day after payment confirmation.
                      </div>
                    </div>
                  )}

                  <div className="mt-4 flex items-center gap-1.5 text-xs text-gray-400">
                    <Lock className="w-3.5 h-3.5"/> 256-bit SSL · PCI DSS Level 1 · 3D Secure
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* ── Navigation ──────────────────────────────────────────────────── */}
          <div className="fixed bottom-0 left-0 right-0 sm:relative sm:bottom-auto z-30 sm:z-auto bg-white sm:bg-transparent border-t border-gray-200 sm:border-0 px-3 py-3 sm:p-0 sm:mt-5">
            <div className="flex items-center gap-3 max-w-5xl mx-auto">
              <button type="button"
                onClick={() => { setError(''); setStep(s => s - 1) }}
                className="flex items-center gap-1.5 px-4 py-3 border border-gray-300 text-gray-600 rounded-xl text-sm font-semibold hover:bg-gray-50 transition-colors touch-manipulation flex-shrink-0">
                <ArrowLeft className="w-4 h-4"/> <span className="hidden sm:inline">Back</span>
              </button>
              <button type="button" onClick={next} disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-700 text-white rounded-xl text-sm font-bold hover:bg-blue-800 disabled:opacity-60 transition-colors touch-manipulation">
                {loading ? (
                  <><Loader2 className="w-4 h-4 animate-spin"/> Processing…</>
                ) : step === 5 ? (
                  <>Submit Application <ArrowRight className="w-4 h-4"/></>
                ) : step === 6 ? (
                  <><Lock className="w-4 h-4"/> Pay {quote ? `AED ${fmt(quote.total_premium)}` : form.total_premium ? `AED ${fmt(form.total_premium)}` : ''}</>
                ) : (
                  <>Continue <ArrowRight className="w-4 h-4"/></>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// ── Confirmation ───────────────────────────────────────────────────────────────

function Confirmation({ policyNumber, applicationNumber, paymentReference, totalPremium, planName, email, onDone }: {
  policyNumber: string; applicationNumber: string; paymentReference: string
  totalPremium: number; planName: string; email: string; onDone: () => void
}) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-start sm:items-center justify-center px-3 py-8 sm:py-0">
      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 max-w-lg w-full p-6 sm:p-8 text-center">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-10 h-10 text-green-600"/>
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-2">Policy Issued!</h1>
        <p className="text-gray-500 text-sm mb-5">
          Your Adamjee Insurance policy is now active. A confirmation email has been sent to <strong>{email}</strong>.
        </p>

        <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5 text-left space-y-3 mb-5">
          {[
            ['Policy Number', policyNumber, true],
            ['Plan', planName, false],
            ['Application', applicationNumber, true],
            ['Payment Ref', paymentReference, true],
            ['Annual Premium', `AED ${totalPremium.toLocaleString('en-AE', { minimumFractionDigits: 2 })}`, false],
          ].map(([label, value, mono]) => (
            <div key={label as string}>
              <p className="text-xs text-gray-400 uppercase tracking-wider">{label as string}</p>
              <p className={`font-bold text-gray-900 ${mono ? 'font-mono text-blue-800' : ''}`}>{value as string}</p>
            </div>
          ))}
        </div>

        <div className="space-y-2 text-sm text-left mb-5">
          {[
            { icon: <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0"/>, text: 'Coverage effective immediately' },
            { icon: <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0"/>, text: 'MEDNET TPA card dispatched within 3 business days' },
            { icon: <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0"/>, text: 'Policy schedule uploaded to member portal' },
            { icon: <FileText className="w-4 h-4 text-blue-500 flex-shrink-0"/>, text: 'Manage your policy anytime via the member portal' },
          ].map(({ icon, text }) => (
            <div key={text} className="flex items-center gap-2.5 text-gray-600">{icon}{text}</div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button onClick={onDone} className="flex-1 py-3 border border-gray-300 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-50 touch-manipulation">
            Back to Home
          </button>
          <Link to="/portal/login"
            className="flex-1 py-3 bg-blue-700 text-white rounded-xl text-sm font-bold hover:bg-blue-800 text-center flex items-center justify-center gap-1.5 touch-manipulation">
            Member Portal <ArrowRight className="w-4 h-4"/>
          </Link>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function Card({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 sm:p-6 md:p-8">
      <h2 className="text-lg sm:text-xl font-extrabold text-gray-900 mb-0.5">{title}</h2>
      <p className="text-xs sm:text-sm text-gray-500 mb-5">{subtitle}</p>
      {children}
    </div>
  )
}

function Field({ label, value, onChange, type = 'text', placeholder }: {
  label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-600 mb-1.5">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"/>
    </div>
  )
}

function SelectField({ label, value, onChange, options, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; options: string[]; placeholder?: string
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-600 mb-1.5">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
        <option value="">{placeholder || 'Select…'}</option>
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">{title}</h3>
      <div className="bg-gray-50 rounded-xl p-3 sm:p-4 space-y-2">{children}</div>
    </div>
  )
}

function RR({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <span className="text-gray-500 flex-shrink-0">{label}</span>
      <span className="font-medium text-gray-900 text-right">{value || '—'}</span>
    </div>
  )
}

function Consent({ checked, onChange, label, readOnly }: {
  checked: boolean; onChange?: (v: boolean) => void; label: string; readOnly?: boolean
}) {
  return (
    <label className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-colors touch-manipulation ${
      checked ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white hover:border-blue-200'
    } ${readOnly ? 'cursor-default' : ''}`}>
      <input type="checkbox" checked={checked} readOnly={readOnly}
        onChange={readOnly ? undefined : e => onChange?.(e.target.checked)}
        className="mt-0.5 w-4 h-4 text-blue-600 rounded flex-shrink-0"/>
      <span className="text-sm text-gray-700 leading-relaxed">{label}</span>
    </label>
  )
}
