import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockList, mockGet } = vi.hoisted(() => ({
  mockList: vi.fn(),
  mockGet: vi.fn(),
}))

vi.mock('../src/services/api', () => ({
  default: {},
  policiesApi: {
    list: mockList,
    get: mockGet,
    renew: vi.fn(),
    generateDocument: vi.fn(),
    listDocuments: vi.fn().mockResolvedValue({ data: { data: [] } }),
  },
  paymentsApi: {
    listByPolicy: vi.fn().mockResolvedValue({ data: { data: [] } }),
    record: vi.fn(),
  },
}))

vi.mock('../src/context/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

import PoliciesPage from '../src/pages/PoliciesPage'

const emptyList = { data: { data: [] } }
const policyList = {
  data: {
    data: [
      {
        id: 'pol1',
        policy_number: 'POL-20260101-ABCDEF',
        customer_name: 'Dave',
        customer_email: 'dave@example.com',
        status: 'active',
        total_premium: '400.00',
        effective_date: '2026-01-01T00:00:00Z',
        expiry_date: '2027-01-01T00:00:00Z',
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
        <PoliciesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('PoliciesPage', () => {
  beforeEach(() => {
    mockList.mockReset()
    mockGet.mockReset()
  })

  it('shows empty state when no policies', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    expect(await screen.findByText(/no policies yet/i)).toBeInTheDocument()
  })

  it('renders a policy row with policy number', async () => {
    mockList.mockResolvedValue(policyList)
    renderPage()
    expect(await screen.findByText('POL-20260101-ABCDEF')).toBeInTheDocument()
    expect(screen.getByText('Dave')).toBeInTheDocument()
  })

  it('shows active status badge', async () => {
    mockList.mockResolvedValue(policyList)
    renderPage()
    await screen.findByText('POL-20260101-ABCDEF')
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('opens policy detail modal on view click', async () => {
    mockList.mockResolvedValue(policyList)
    mockGet.mockResolvedValue({
      data: {
        data: {
          ...policyList.data.data[0],
          member_count: 1,
          items: [],
          members: [],
        },
      },
    })
    renderPage()
    await screen.findByText('POL-20260101-ABCDEF')
    fireEvent.click(screen.getByRole('button', { name: /view/i }))
    expect(await screen.findByText('Policy Details')).toBeInTheDocument()
  })
})
