import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, TrendingUp } from 'lucide-react'
import { paymentsApi } from '../services/api'
import { Payment } from '../types'
import PageHeader from '../components/PageHeader'
import StatusBadge from '../components/StatusBadge'

const METHOD_LABELS: Record<string, string> = {
  bank_transfer: 'Bank Transfer',
  card: 'Card',
  upi: 'UPI',
  wallet: 'Wallet',
  cheque: 'Cheque',
  cash: 'Cash',
  net_banking: 'Net Banking',
}

export default function PaymentsPage() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['all-payments', page],
    queryFn: () => paymentsApi.listAll(page).then(r => r.data),
  })

  const payments: Payment[] = data?.data ?? []
  const pagination = data?.pagination ?? { total: 0, page: 1, per_page: 20, total_pages: 1 }

  const totalCollected = payments
    .filter(p => p.status === 'success')
    .reduce((sum, p) => sum + parseFloat(p.amount), 0)

  return (
    <div className="p-6">
      <PageHeader
        title="Payments"
        subtitle={`${pagination.total} payment records`}
      />

      {/* Summary card */}
      {payments.length > 0 && (
        <div className="mb-6 grid grid-cols-2 gap-4 max-w-md">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <TrendingUp className="w-4 h-4" />
              This page total
            </div>
            <p className="text-2xl font-bold text-gray-900">
              ${totalCollected.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-gray-500 text-sm mb-1">Total records</p>
            <p className="text-2xl font-bold text-gray-900">{pagination.total}</p>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Payment #</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Policy ID</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Amount</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Method</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Reference</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">Paid At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading…</td>
              </tr>
            ) : payments.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">No payments recorded yet</td>
              </tr>
            ) : payments.map(payment => (
              <tr key={payment.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-gray-700">{payment.payment_number}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-500 max-w-[120px] truncate">
                  {payment.policy_id}
                </td>
                <td className="px-4 py-3 font-semibold text-gray-900">
                  ${parseFloat(payment.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {METHOD_LABELS[payment.method] ?? payment.method}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {payment.reference ?? <span className="text-gray-300">—</span>}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={payment.status} />
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(payment.paid_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {pagination.total_pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between text-sm text-gray-600">
            <span>Page {pagination.page} of {pagination.total_pages} · {pagination.total} total</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={pagination.page === 1}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
                disabled={pagination.page === pagination.total_pages}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
