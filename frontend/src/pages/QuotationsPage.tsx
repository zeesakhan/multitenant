import { useState, FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FileSearch, Send, ArrowRight, Clock } from 'lucide-react'
import { quotationsApi, productsApi, plansApi, applicationsApi } from '../services/api'
import PageHeader from '../components/PageHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import Modal from '../components/Modal'
import { Quote, Product, Plan } from '../types'

const STATUS_TABS = ['all', 'draft', 'sent', 'viewed', 'expired', 'converted', 'declined'] as const
type StatusTab = typeof STATUS_TABS[number]

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    draft:     'bg-gray-100 text-gray-600',
    sent:      'bg-blue-100 text-blue-700',
    viewed:    'bg-purple-100 text-purple-700',
    expired:   'bg-red-100 text-red-600',
    converted: 'bg-green-100 text-green-700',
    declined:  'bg-orange-100 text-orange-700',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${styles[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}

function isExpired(validUntil: string) {
  return new Date(validUntil) < new Date()
}

function errMsg(err: unknown) {
  const d = (err as { response?: { data?: { errors?: { message: string }[]; detail?: string } } })?.response?.data
  return d?.errors?.[0]?.message ?? d?.detail ?? 'Something went wrong.'
}

// ── New Quote Modal ────────────────────────────────────────────────────────────

function NewQuoteModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({
    product_id: '', plan_id: '', customer_name: '', customer_email: '',
  })
  const [error, setError] = useState('')

  const productsQuery = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.list(1),
    enabled: open,
  })

  const plansQuery = useQuery({
    queryKey: ['plans', form.product_id],
    queryFn: () => plansApi.list(form.product_id),
    enabled: !!form.product_id,
  })

  const products: Product[] = productsQuery.data?.data?.data ?? productsQuery.data?.data?.items ?? []
  const plans: Plan[] = plansQuery.data?.data?.data ?? plansQuery.data?.data?.items ?? []
  const selectedPlan = plans.find((p) => p.id === form.plan_id)

  const mutation = useMutation({
    mutationFn: () => quotationsApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] })
      onClose()
      setForm({ product_id: '', plan_id: '', customer_name: '', customer_email: '' })
      setError('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const handleProductChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setForm((f) => ({ ...f, product_id: e.target.value, plan_id: '' }))
  }

  return (
    <Modal open={open} onClose={onClose} title="New Quote">
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      <form
        onSubmit={(e: FormEvent) => { e.preventDefault(); setError(''); mutation.mutate() }}
        className="space-y-4"
      >
        {/* Product */}
        <div>
          <label className="label">Product <span className="text-red-500">*</span></label>
          {productsQuery.isLoading
            ? <p className="text-sm text-gray-400">Loading products...</p>
            : (
              <select className="input" value={form.product_id} onChange={handleProductChange} required>
                <option value="">Select a product...</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            )}
        </div>

        {/* Plan */}
        <div>
          <label className="label">Plan <span className="text-red-500">*</span></label>
          {!form.product_id
            ? <p className="text-sm text-gray-400 italic">Select a product first.</p>
            : plansQuery.isLoading
              ? <p className="text-sm text-gray-400">Loading plans...</p>
              : plans.length === 0
                ? <p className="text-sm text-red-500">No active plans for this product. Add plans first.</p>
                : (
                  <select className="input" value={form.plan_id}
                    onChange={(e) => setForm((f) => ({ ...f, plan_id: e.target.value }))} required>
                    <option value="">Select a plan...</option>
                    {plans.filter((p) => p.is_active).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {p.plan_type} (${Number(p.base_premium).toFixed(2)}/mo)
                      </option>
                    ))}
                  </select>
                )
          }
        </div>

        {/* Premium preview */}
        {selectedPlan && (
          <div className="flex items-center justify-between px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg">
            <span className="text-sm text-emerald-700">Estimated Premium</span>
            <span className="text-xl font-bold text-emerald-700">
              ${Number(selectedPlan.base_premium).toFixed(2)}
              <span className="text-sm font-normal">/mo</span>
            </span>
          </div>
        )}

        {/* Customer */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Customer Name <span className="text-red-500">*</span></label>
            <input className="input" value={form.customer_name}
              onChange={(e) => setForm((f) => ({ ...f, customer_name: e.target.value }))}
              placeholder="Jane Smith" required />
          </div>
          <div>
            <label className="label">Customer Email <span className="text-red-500">*</span></label>
            <input className="input" type="email" value={form.customer_email}
              onChange={(e) => setForm((f) => ({ ...f, customer_email: e.target.value }))}
              placeholder="jane@example.com" required />
          </div>
        </div>

        <p className="text-xs text-gray-400">Quote will be valid for 30 days from creation.</p>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn-primary" disabled={mutation.isPending || !form.plan_id}>
            {mutation.isPending ? 'Creating...' : 'Create Quote'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

// ── Quote Detail / Action Modal ────────────────────────────────────────────────

function QuoteDetailModal({ quoteId, onClose }: { quoteId: string; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const [sendEmail, setSendEmail] = useState('')
  const [showSendForm, setShowSendForm] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['quote', quoteId],
    queryFn: () => quotationsApi.get(quoteId),
  })

  const quote: Quote | undefined = data?.data?.data

  const sendMut = useMutation({
    mutationFn: () => quotationsApi.send(quoteId, sendEmail || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] })
      queryClient.invalidateQueries({ queryKey: ['quote', quoteId] })
      setShowSendForm(false)
      setSendEmail('')
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const convertMut = useMutation({
    mutationFn: () => applicationsApi.create({
      quote_id: quoteId,
      product_id: quote!.product_id,
      plan_id: quote!.plan_id,
      customer_name: quote!.customer_name,
      customer_email: quote!.customer_email,
      member_count: 1,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] })
      queryClient.invalidateQueries({ queryKey: ['applications'] })
      onClose()
    },
    onError: (err: unknown) => { setError(errMsg(err)) },
  })

  const isWorking = sendMut.isPending || convertMut.isPending

  return (
    <Modal open={true} onClose={onClose} title="Quote Details" size="md">
      {isLoading && <LoadingSpinner />}
      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}

      {quote && (
        <div className="space-y-4">
          {/* Header info */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Quote #', quote.quote_number],
              ['Customer', quote.customer_name],
              ['Email', quote.customer_email],
              ['Premium', `$${Number(quote.total_premium).toFixed(2)}/mo`],
              ['Status', null],
              ['Valid Until', new Date(quote.valid_until).toLocaleDateString()],
            ].map(([label, value]) => (
              <div key={label as string} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">{label}</p>
                {value !== null
                  ? <p className="font-medium text-gray-900">{value}</p>
                  : <div className="flex items-center gap-2">
                      {statusBadge(quote.status)}
                      {isExpired(quote.valid_until) && quote.status === 'sent' && (
                        <span className="text-xs text-red-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> expired
                        </span>
                      )}
                    </div>
                }
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="border-t border-gray-200 pt-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Actions</p>

            {/* DRAFT → send */}
            {quote.status === 'draft' && (
              <div className="space-y-3">
                {!showSendForm
                  ? (
                    <button
                      onClick={() => setShowSendForm(true)}
                      disabled={isWorking}
                      className="btn-primary w-full justify-center gap-2"
                    >
                      <Send className="w-4 h-4" /> Send Quote to Customer
                    </button>
                  )
                  : (
                    <div className="space-y-2">
                      <label className="label">Recipient Email</label>
                      <input
                        className="input"
                        type="email"
                        value={sendEmail}
                        onChange={(e) => setSendEmail(e.target.value)}
                        placeholder={quote.customer_email}
                      />
                      <p className="text-xs text-gray-400">Leave blank to send to {quote.customer_email}</p>
                      <div className="flex gap-2">
                        <button
                          onClick={() => sendMut.mutate()}
                          disabled={isWorking}
                          className="btn-primary flex-1 justify-center gap-2"
                        >
                          <Send className="w-4 h-4" />
                          {sendMut.isPending ? 'Sending...' : 'Confirm Send'}
                        </button>
                        <button onClick={() => setShowSendForm(false)} className="btn-secondary">
                          Cancel
                        </button>
                      </div>
                    </div>
                  )
                }
              </div>
            )}

            {/* SENT / VIEWED → convert to application */}
            {(quote.status === 'sent' || quote.status === 'viewed') && (
              <div className="space-y-2">
                <button
                  onClick={() => convertMut.mutate()}
                  disabled={isWorking}
                  className="btn-primary w-full justify-center gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  <ArrowRight className="w-4 h-4" />
                  {convertMut.isPending ? 'Converting...' : 'Convert to Application'}
                </button>
                <p className="text-xs text-gray-400 text-center">
                  Creates a draft application for {quote.customer_name} with this quote's product &amp; plan.
                </p>
              </div>
            )}

            {/* Final states */}
            {['expired', 'converted', 'declined'].includes(quote.status) && (
              <p className="text-sm text-gray-500 italic">
                No further actions available for a <strong>{quote.status}</strong> quote.
              </p>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function QuotationsPage() {
  const [showNew, setShowNew] = useState(false)
  const [viewingId, setViewingId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<StatusTab>('all')

  const { data, isLoading, error } = useQuery({
    queryKey: ['quotations'],
    queryFn: () => quotationsApi.list(1),
  })

  const allQuotes: Quote[] = data?.data?.data ?? data?.data?.items ?? []
  const quotes = activeTab === 'all'
    ? allQuotes
    : allQuotes.filter((q) => q.status === activeTab)

  const counts = STATUS_TABS.reduce((acc, s) => {
    acc[s] = s === 'all' ? allQuotes.length : allQuotes.filter((q) => q.status === s).length
    return acc
  }, {} as Record<StatusTab, number>)

  return (
    <div className="p-8">
      <PageHeader
        title="Quotations"
        subtitle="Create and track insurance quotes for customers"
        action={
          <button className="btn-primary" onClick={() => setShowNew(true)}>
            <Plus className="w-4 h-4" /> New Quote
          </button>
        }
      />

      {/* Status tabs */}
      <div className="flex gap-1 mb-5 bg-gray-100 p-1 rounded-xl w-fit">
        {STATUS_TABS.map((tab) => (
          counts[tab] > 0 || tab === 'all'
            ? (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize ${
                  activeTab === tab
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
                {counts[tab] > 0 && (
                  <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-xs ${
                    activeTab === tab ? 'bg-primary-100 text-primary-700' : 'bg-gray-200 text-gray-600'
                  }`}>
                    {counts[tab]}
                  </span>
                )}
              </button>
            )
            : null
        ))}
      </div>

      {isLoading && <LoadingSpinner />}
      {error && <ErrorMessage message="Failed to load quotations." />}

      {!isLoading && !error && quotes.length === 0 && (
        <div className="card flex flex-col items-center justify-center py-16 text-center">
          <FileSearch className="w-12 h-12 text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            {activeTab === 'all' ? 'No quotes yet' : `No ${activeTab} quotes`}
          </h3>
          <p className="text-sm text-gray-500 mb-4 max-w-sm">
            {activeTab === 'all'
              ? 'Create a quote to start the customer journey.'
              : 'Try a different status filter.'}
          </p>
          {activeTab === 'all' && (
            <button className="btn-primary" onClick={() => setShowNew(true)}>
              <Plus className="w-4 h-4" /> New Quote
            </button>
          )}
        </div>
      )}

      {!isLoading && !error && quotes.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Quote #', 'Customer', 'Email', 'Premium', 'Status', 'Valid Until', 'Created', 'Actions'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {quotes.map((q) => (
                <tr key={q.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-600 font-medium">{q.quote_number}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{q.customer_name}</td>
                  <td className="px-4 py-3 text-gray-600">{q.customer_email}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    ${Number(q.total_premium).toFixed(2)}
                    <span className="text-xs text-gray-400 font-normal">/mo</span>
                  </td>
                  <td className="px-4 py-3">{statusBadge(q.status)}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(q.valid_until).toLocaleDateString()}
                    {isExpired(q.valid_until) && q.status !== 'converted' && q.status !== 'declined' && (
                      <span className="ml-1 text-red-400">(expired)</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(q.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setViewingId(q.id)}
                      className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                    >
                      View / Act
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <NewQuoteModal open={showNew} onClose={() => setShowNew(false)} />
      {viewingId && <QuoteDetailModal quoteId={viewingId} onClose={() => setViewingId(null)} />}
    </div>
  )
}
