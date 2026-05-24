import { useNavigate, Link } from 'react-router-dom'
import { ShieldCheck, CheckCircle, Phone, Mail, Globe, Star, Users, HeartHandshake, ArrowRight } from 'lucide-react'

const PLANS_PREVIEW = [
  { name: 'GOLD', price: 'AED 4,500', desc: 'Top-tier hospitals across UAE' },
  { name: 'SILVER PREMIUM', price: 'AED 3,400', desc: 'Premium private hospital network' },
  { name: 'SILVER CLASSIC', price: 'AED 2,600', desc: 'Classic private hospital access' },
  { name: 'EMERALD', price: 'AED 2,100', desc: 'Mid-tier comprehensive coverage' },
  { name: 'PEARL', price: 'AED 1,800', desc: 'Solid private clinic network' },
  { name: 'GREEN', price: 'AED 1,500', desc: 'Government + private clinics' },
  { name: 'SILK ROAD', price: 'AED 1,200', desc: 'Essential DHA coverage' },
]

const FEATURES = [
  { icon: ShieldCheck, label: 'DHA Compliant', desc: 'Meets all Dubai Health Authority requirements' },
  { icon: Star, label: 'MEDNET TPA', desc: 'Leading TPA network across UAE' },
  { icon: Users, label: 'Family Coverage', desc: 'Cover spouse, children & parents' },
  { icon: HeartHandshake, label: 'AED 1M Annual Limit', desc: 'Per person per year' },
]

export default function AdamjeeLandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-700 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-blue-800 text-lg">Adamjee Insurance</span>
              <span className="ml-2 text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-semibold">UAE</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <a href="tel:+97142XXXXXX" className="hidden md:flex items-center gap-1 text-gray-500 hover:text-blue-700">
              <Phone className="w-3.5 h-3.5" /> +971-4-XXX-XXXX
            </a>
            <Link to="/portal/login" className="text-gray-500 hover:text-blue-700">Member Login</Link>
            <button
              onClick={() => navigate('/buy/adamjee/buy')}
              className="px-4 py-2 bg-blue-700 text-white text-sm font-semibold rounded-lg hover:bg-blue-800 transition-colors"
            >
              Get a Quote
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-800 via-blue-700 to-blue-900 text-white">
        <div className="max-w-7xl mx-auto px-6 py-20 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-blue-600/40 text-blue-100 text-xs font-semibold px-3 py-1.5 rounded-full mb-5">
              <ShieldCheck className="w-3.5 h-3.5" /> DHA Compliant · ISA Licensed · MEDNET TPA
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight mb-5">
              Protect Your Family<br />
              <span className="text-amber-400">with Adamjee Insurance</span>
            </h1>
            <p className="text-blue-100 text-lg mb-8 leading-relaxed">
              Comprehensive health insurance compliant with UAE law. 7 network tiers to fit every
              budget. Annual limit AED 1,000,000 per person. Apply online in minutes.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => navigate('/buy/adamjee/buy')}
                className="flex items-center justify-center gap-2 px-8 py-3.5 bg-amber-400 text-blue-900 font-bold rounded-xl hover:bg-amber-300 transition-colors text-base"
              >
                Buy Now <ArrowRight className="w-5 h-5" />
              </button>
              <a
                href="#plans"
                className="flex items-center justify-center gap-2 px-8 py-3.5 border-2 border-white/40 text-white font-semibold rounded-xl hover:border-white/80 transition-colors text-base"
              >
                View Plans
              </a>
            </div>
          </div>

          {/* Trust card */}
          <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20">
            <h3 className="text-white font-bold text-lg mb-4">Why Adamjee?</h3>
            <div className="space-y-4">
              {[
                'DHA-compliant plans for all Dubai residents',
                'Global coverage — worldwide emergency treatment',
                'No waiting period for emergency care',
                'Pre-existing conditions covered (sub-limit applies)',
                'Maternity, dental, and alternative medicine covered',
                'Fast claim settlement through MEDNET TPA',
                'Digital policy — paperless, instant issuance',
              ].map((item) => (
                <div key={item} className="flex items-start gap-3">
                  <CheckCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  <span className="text-blue-50 text-sm">{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Feature cards */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
            {FEATURES.map(({ icon: Icon, label, desc }) => (
              <div key={label} className="bg-white rounded-2xl p-5 text-center shadow-sm border border-gray-100">
                <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Icon className="w-6 h-6 text-blue-700" />
                </div>
                <p className="font-bold text-gray-800 text-sm mb-1">{label}</p>
                <p className="text-xs text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Plans preview */}
      <section id="plans" className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-extrabold text-gray-900">Choose Your Network Tier</h2>
            <p className="text-gray-500 mt-2">All plans include the same DHA-mandated benefits. Network access varies by tier.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
            {PLANS_PREVIEW.map((plan, i) => (
              <div
                key={plan.name}
                className={`rounded-2xl border p-5 relative transition-all hover:shadow-md cursor-pointer ${
                  i === 0 ? 'border-amber-400 bg-amber-50' : 'border-gray-200 bg-white hover:border-blue-300'
                }`}
                onClick={() => navigate('/buy/adamjee/buy')}
              >
                {i === 0 && (
                  <span className="absolute -top-3 left-4 bg-amber-400 text-blue-900 text-xs font-bold px-3 py-1 rounded-full">
                    BEST COVERAGE
                  </span>
                )}
                <p className="font-bold text-blue-800 mb-1">{plan.name}</p>
                <p className="text-2xl font-extrabold text-gray-900">{plan.price}</p>
                <p className="text-xs text-gray-400 mb-3">/year per person</p>
                <p className="text-xs text-gray-600">{plan.desc}</p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <button
              onClick={() => navigate('/buy/adamjee/buy')}
              className="inline-flex items-center gap-2 px-8 py-3.5 bg-blue-700 text-white font-bold rounded-xl hover:bg-blue-800 transition-colors"
            >
              Compare Plans & Buy <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Coverage highlights */}
      <section className="py-16 bg-blue-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-extrabold text-gray-900 mb-8 text-center">What's Covered</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {[
              { title: 'Inpatient Hospitalization', body: 'Private room, ICU, surgeon, anaesthetist, organ transplant — up to AED 1,000,000 annually.' },
              { title: 'Outpatient Services', body: 'GP & specialist consultations. 20% co-pay (max AED 50). Lab tests & pharmacy at 0% co-pay.' },
              { title: 'Maternity', body: 'Normal and caesarean delivery — AED 10,000 each. Newborn covered for first 30 days.' },
              { title: 'Dental', body: 'Annual dental sub-limit AED 3,500 with 20% co-pay for eligible treatments.' },
              { title: 'Physiotherapy', body: 'Up to 15 sessions per year with 0% co-pay. Includes rehabilitation therapy.' },
              { title: 'Pre-existing Conditions', body: 'All declared chronic & pre-existing conditions covered with AED 150,000 sub-limit.' },
              { title: 'Alternative Medicine', body: 'Homeopathy, acupuncture, chiropractic up to AED 1,600/year on reimbursement basis.' },
              { title: 'Mental Health', body: 'Emergency mental health treatments covered under standard benefits.' },
              { title: 'Repatriation', body: 'Repatriation of mortal remains up to AED 7,500. Emergency ambulance included.' },
            ].map(({ title, body }) => (
              <div key={title} className="bg-white rounded-xl p-5 border border-blue-100 shadow-sm">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-gray-900 text-sm mb-1">{title}</p>
                    <p className="text-xs text-gray-500 leading-relaxed">{body}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-blue-800 text-white text-center">
        <div className="max-w-2xl mx-auto px-6">
          <h2 className="text-3xl font-extrabold mb-3">Ready to protect your family?</h2>
          <p className="text-blue-200 mb-8">
            Apply online in under 10 minutes. Instant policy issuance after payment.
          </p>
          <button
            onClick={() => navigate('/buy/adamjee/buy')}
            className="px-10 py-4 bg-amber-400 text-blue-900 font-bold rounded-xl hover:bg-amber-300 transition-colors text-lg"
          >
            Start Your Application
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
          <p>© 2026 Adamjee Insurance. Licensed by the Insurance Authority of UAE.</p>
          <div className="flex items-center gap-5">
            <a href="mailto:customercare@adamjeeinsurance.ae" className="flex items-center gap-1 hover:text-white">
              <Mail className="w-3.5 h-3.5" /> customercare@adamjeeinsurance.ae
            </a>
            <a href="https://adamjeeinsurance.ae" target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-white">
              <Globe className="w-3.5 h-3.5" /> adamjeeinsurance.ae
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
