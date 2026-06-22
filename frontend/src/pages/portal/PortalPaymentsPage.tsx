import { useQuery } from '@tanstack/react-query'
import { CreditCard, TrendingUp } from 'lucide-react'
import { portalCustomerApi } from '../../services/portalApi'

const METHOD_LABELS: Record<string, string> = {
  bank_transfer: 'Bank Transfer', card: 'Card', cash: 'Cash',
  cheque: 'Cheque', upi: 'UPI', wallet: 'Wallet', net_banking: 'Net Banking',
}

const STATUS_COLORS: Record<string, string> = {
  success: 'bg-green-100 text-green-700',
  pending: 'bg-amber-100 text-amber-700',
  failed: 'bg-red-100 text-red-700',
  refunded: 'bg-blue-100 text-blue-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

function fmt(n: string | number) {
  return Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export default function PortalPaymentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['portal-payments'],
    queryFn: portalCustomerApi.getPayments,
    retry: false,
  })

  const raw = data?.data?.data
  const payments: Record<string, unknown>[] = raw?.payments ?? []
  const totalPaid: number = raw?.total_paid ?? 0

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
        <p className="text-gray-500 text-sm mt-1">Your premium payment history.</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 max-w-sm mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
            <TrendingUp className="w-4 h-4" /> Total paid
          </div>
          <p className="text-2xl font-bold text-gray-900">AED {fmt(totalPaid)}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
            <CreditCard className="w-4 h-4" /> Payments
          </div>
          <p className="text-2xl font-bold text-gray-900">{payments.length}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <p className="p-6 text-sm text-gray-400">Loading payments…</p>
        ) : payments.length === 0 ? (
          <p className="p-10 text-center text-sm text-gray-400">No payments recorded yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Payment #', 'Amount', 'Method', 'Reference', 'Status', 'Date'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-medium text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {payments.map((p) => (
                <tr key={String(p.id)} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{String(p.payment_number)}</td>
                  <td className="px-4 py-3 font-semibold text-gray-900">AED {fmt(String(p.amount))}</td>
                  <td className="px-4 py-3 text-gray-600">{METHOD_LABELS[String(p.method)] ?? String(p.method)}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{String(p.reference ?? '—')}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${STATUS_COLORS[String(p.status)] ?? 'bg-gray-100 text-gray-500'}`}>
                      {String(p.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {p.paid_at ? new Date(String(p.paid_at)).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
