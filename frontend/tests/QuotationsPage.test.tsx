import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockList, mockCreate } = vi.hoisted(() => ({
  mockList: vi.fn(),
  mockCreate: vi.fn(),
}))

vi.mock('../src/services/api', () => ({
  default: {},
  quotationsApi: {
    list: mockList,
    create: mockCreate,
    get: vi.fn(),
    send: vi.fn(),
  },
  productsApi: { list: vi.fn().mockResolvedValue({ data: { data: [] } }) },
  plansApi: { list: vi.fn().mockResolvedValue({ data: { data: [] } }) },
  applicationsApi: { create: vi.fn() },
}))

vi.mock('../src/context/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

import QuotationsPage from '../src/pages/QuotationsPage'

const emptyList = { data: { data: [] } }
const quoteList = {
  data: {
    data: [
      {
        id: 'q1',
        quote_number: 'QT-001',
        customer_name: 'Alice',
        customer_email: 'alice@example.com',
        status: 'draft',
        total_premium: '250.00',
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
  },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <QuotationsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('QuotationsPage', () => {
  beforeEach(() => {
    mockList.mockReset()
    mockCreate.mockReset()
  })

  it('shows empty state when no quotes exist', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    expect(await screen.findByText(/no quotes yet/i)).toBeInTheDocument()
  })

  it('renders a quote row when data is returned', async () => {
    mockList.mockResolvedValue(quoteList)
    renderPage()
    expect(await screen.findByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('QT-001')).toBeInTheDocument()
  })

  it('opens new-quote modal with title', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    await screen.findByText(/no quotes yet/i)
    fireEvent.click(screen.getAllByRole('button', { name: /new quote/i })[0])
    expect(await screen.findByRole('heading', { name: 'New Quote' })).toBeInTheDocument()
  })

  it('shows $250 premium in quote row', async () => {
    mockList.mockResolvedValue(quoteList)
    renderPage()
    expect(await screen.findByText(/250/)).toBeInTheDocument()
  })
})
