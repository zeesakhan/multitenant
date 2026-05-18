import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockListAll } = vi.hoisted(() => ({ mockListAll: vi.fn() }))

vi.mock('../src/services/api', () => ({
  default: {},
  paymentsApi: { listAll: mockListAll, record: vi.fn(), listByPolicy: vi.fn() },
}))

import PaymentsPage from '../src/pages/PaymentsPage'

const emptyResponse = { data: [], pagination: { total: 0, page: 1, per_page: 20, total_pages: 1 } }
const paymentResponse = {
  data: [
    {
      id: 'pay1',
      payment_number: 'PAY-001',
      policy_id: 'pol-abc12345',
      amount: '400.00',
      method: 'bank_transfer',
      status: 'success',
      reference: 'REF-XYZ',
      paid_at: '2026-02-01T10:00:00Z',
    },
  ],
  pagination: { total: 1, page: 1, per_page: 20, total_pages: 1 },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><PaymentsPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('PaymentsPage', () => {
  beforeEach(() => mockListAll.mockReset())

  it('renders page header', async () => {
    mockListAll.mockResolvedValue({ data: emptyResponse })
    renderPage()
    expect(await screen.findByText('Payments')).toBeInTheDocument()
  })

  it('shows a payment row', async () => {
    mockListAll.mockResolvedValue({ data: paymentResponse })
    renderPage()
    expect(await screen.findByText('PAY-001')).toBeInTheDocument()
    expect(screen.getAllByText('$400.00').length).toBeGreaterThan(0)
  })

  it('shows payment method label', async () => {
    mockListAll.mockResolvedValue({ data: paymentResponse })
    renderPage()
    await screen.findByText('PAY-001')
    expect(screen.getByText('Bank Transfer')).toBeInTheDocument()
  })

  it('shows empty message when no payments', async () => {
    mockListAll.mockResolvedValue({ data: emptyResponse })
    renderPage()
    expect(await screen.findByText(/no payments recorded yet/i)).toBeInTheDocument()
  })
})
