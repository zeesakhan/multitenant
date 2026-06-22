import { useEffect, useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { Heart, ShieldCheck, ArrowRight, CheckCircle, Users, ChevronDown, ChevronUp } from 'lucide-react'
import { buyApiService } from '../../services/buyApi'

const PLAN_TYPE_LABELS: Record<string, string> = {
  individual: 'Individual', family: 'Family', group: 'Group', senior: 'Senior',
}

const COVERAGE_TYPE_LABELS: Record<string, string> = {
  hospitalization: 'Hospitalization', outpatient: 'Outpatient', dental: 'Dental',
  vision: 'Vision', maternity: 'Maternity', mental_health: 'Mental Health',
  prescription: 'Prescription', preventive: 'Preventive', emergency: 'Emergency', wellness: 'Wellness',
}

function fmt(n: string | number) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

interface Coverage {
  id: string; name: string; coverage_type: string; limit_amount: string | null; copay: string | null
}

interface Plan {
  id: string; name: string; code: string; plan_type: string
  base_premium: string; description: string | null; coverages: Coverage[]
}

interface Product {
  id: string; name: string; code: string; description: string | null; plans: Plan[]
}

export default function BuyProductsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { tenantId, tenantName } = (location.state as { tenantId: string; tenantName: string }) ?? {}

  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  useEffect(() => {
    if (!tenantId) { navigate('/buy'); return }
    buyApiService.getProducts(tenantId)
      .then((r) => setProducts(r.data.data ?? []))
      .catch(() => setError('Failed to load plans. Please try again.'))
      .finally(() => setLoading(false))
  }, [tenantId, navigate])

  function toggleExpand(planId: string) {
    setExpanded((prev) => ({ ...prev, [planId]: !prev[planId] }))
  }

  if (!tenantId) return null

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

      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900">Available Plans</h1>
          <p className="text-gray-500 mt-1">Choose the plan that's right for you and your family.</p>
        </div>

        {loading && (
          <div className="text-center py-20 text-gray-400 text-sm">Loading plans…</div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">{error}</div>
        )}

        {!loading && !error && products.length === 0 && (
          <div className="text-center py-20">
            <ShieldCheck className="w-12 h-12 text-gray-200 mx-auto mb-3" />
            <p className="text-gray-400">No active plans available. Please contact your insurer.</p>
          </div>
        )}

        {products.map((product) => (
          <div key={product.id} className="mb-8">
            <div className="mb-4">
              <h2 className="text-xl font-bold text-gray-800">{product.name}</h2>
              {product.description && <p className="text-sm text-gray-500 mt-0.5">{product.description}</p>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {product.plans.map((plan) => (
                <div
                  key={plan.id}
                  className="bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:border-emerald-300 transition-all flex flex-col"
                >
                  {/* Plan header */}
                  <div className="p-6 flex-1">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                          {PLAN_TYPE_LABELS[plan.plan_type] ?? plan.plan_type}
                        </span>
                        <h3 className="text-lg font-bold text-gray-900 mt-2">{plan.name}</h3>
                        {plan.description && (
                          <p className="text-xs text-gray-500 mt-1 leading-relaxed">{plan.description}</p>
                        )}
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Starting from</p>
                      <p className="text-3xl font-extrabold text-gray-900">
                        AED {fmt(plan.base_premium)}
                        <span className="text-sm font-normal text-gray-400">/yr</span>
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                        <Users className="w-3 h-3" /> Per primary insured · dependents discounted
                      </p>
                    </div>

                    {/* Coverage list */}
                    {plan.coverages.length > 0 && (
                      <div>
                        <ul className="space-y-1.5">
                          {(expanded[plan.id] ? plan.coverages : plan.coverages.slice(0, 4)).map((c) => (
                            <li key={c.id} className="flex items-center gap-2 text-xs text-gray-600">
                              <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                              <span className="font-medium">{c.name}</span>
                              {c.limit_amount && (
                                <span className="ml-auto text-gray-400 whitespace-nowrap">
                                  up to AED {fmt(c.limit_amount)}
                                </span>
                              )}
                            </li>
                          ))}
                        </ul>
                        {plan.coverages.length > 4 && (
                          <button
                            onClick={() => toggleExpand(plan.id)}
                            className="mt-2 flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                          >
                            {expanded[plan.id] ? (
                              <><ChevronUp className="w-3.5 h-3.5" /> Show less</>
                            ) : (
                              <><ChevronDown className="w-3.5 h-3.5" /> +{plan.coverages.length - 4} more coverages</>
                            )}
                          </button>
                        )}
                      </div>
                    )}
                  </div>

                  {/* CTA */}
                  <div className="p-4 border-t border-gray-100">
                    <button
                      onClick={() => navigate('/buy/apply', {
                        state: { tenantId, tenantName, plan, productName: product.name },
                      })}
                      className="w-full flex items-center justify-center gap-2 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-colors"
                    >
                      Apply Now <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
