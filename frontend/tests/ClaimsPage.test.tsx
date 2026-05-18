import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockList } = vi.hoisted(() => ({ mockList: vi.fn() }))

vi.mock('../src/services/api', () => ({
  default: {},
  claimsApi: {
    list: mockList,
    create: vi.fn(),
    get: vi.fn(),
    update: vi.fn(),
    startReview: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    pay: vi.fn(),
  },
  policiesApi: { list: vi.fn().mockResolvedValue({ data: { data: [] } }) },
}))

vi.mock('../src/context/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

import ClaimsPage from '../src/pages/ClaimsPage'

const emptyList = { data: { data: [] } }
const claimList = {
  data: {
    data: [
      {
        id: 'cl1',
        claim_number: 'CLM-001',
        policy_id: 'pol-00000001',
        claim_type: 'medical',
        customer_name: 'Carol',
        claimed_amount: '1500.00',
        approved_amount: null,
        status: 'submitted',
        incident_date: '2026-01-10',
        created_at: '2026-01-11T00:00:00Z',
      },
    ],
  },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ClaimsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ClaimsPage', () => {
  beforeEach(() => mockList.mockReset())

  it('shows empty state when no claims', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    expect(await screen.findByText(/no claims yet/i)).toBeInTheDocument()
  })

  it('renders a claim row with claim number', async () => {
    mockList.mockResolvedValue(claimList)
    renderPage()
    expect(await screen.findByText('CLM-001')).toBeInTheDocument()
    expect(screen.getAllByText('$1500.00').length).toBeGreaterThan(0)
  })

  it('opens file-claim modal', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    await screen.findByText(/no claims yet/i)
    fireEvent.click(screen.getAllByRole('button', { name: /file claim/i })[0])
    expect(await screen.findByText('File New Claim')).toBeInTheDocument()
  })

  it('shows status badge for submitted claim', async () => {
    mockList.mockResolvedValue(claimList)
    renderPage()
    await screen.findByText('CLM-001')
    expect(screen.getByText('submitted')).toBeInTheDocument()
  })
})
