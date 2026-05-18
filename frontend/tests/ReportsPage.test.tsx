import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockSummary, mockApplications, mockPremium, mockClaims } = vi.hoisted(() => ({
  mockSummary: vi.fn(),
  mockApplications: vi.fn(),
  mockPremium: vi.fn(),
  mockClaims: vi.fn(),
}))

vi.mock('../src/services/api', () => ({
  default: {},
  reportsApi: {
    summary: mockSummary,
    applications: mockApplications,
    premium: mockPremium,
    claims: mockClaims,
  },
}))

import ReportsPage from '../src/pages/ReportsPage'

const summaryResponse = {
  data: {
    data: {
      active_policies: 10,
      expiring_soon_30d: 2,
      pending_applications: 5,
      open_claims: 3,
      monthly_premium_due: 5000,
      collected_this_month: 4200,
      claims_paid_this_month: 800,
    },
  },
}

const emptyRows = { data: { data: [] } }

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><ReportsPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ReportsPage', () => {
  beforeEach(() => {
    mockSummary.mockReset()
    mockApplications.mockReset()
    mockPremium.mockReset()
    mockClaims.mockReset()
  })

  it('renders page header', async () => {
    mockSummary.mockResolvedValue(summaryResponse)
    mockApplications.mockResolvedValue(emptyRows)
    mockPremium.mockResolvedValue(emptyRows)
    mockClaims.mockResolvedValue(emptyRows)
    renderPage()
    expect(await screen.findByText('Reports')).toBeInTheDocument()
  })

  it('shows active policies KPI', async () => {
    mockSummary.mockResolvedValue(summaryResponse)
    mockApplications.mockResolvedValue(emptyRows)
    mockPremium.mockResolvedValue(emptyRows)
    mockClaims.mockResolvedValue(emptyRows)
    renderPage()
    expect(await screen.findByText('10')).toBeInTheDocument()
    expect(screen.getByText('Active Policies')).toBeInTheDocument()
  })

  it('shows expiring soon KPI', async () => {
    mockSummary.mockResolvedValue(summaryResponse)
    mockApplications.mockResolvedValue(emptyRows)
    mockPremium.mockResolvedValue(emptyRows)
    mockClaims.mockResolvedValue(emptyRows)
    renderPage()
    await screen.findByText('Reports')
    expect(screen.getByText('Expiring (30d)')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows no data message when summary missing', async () => {
    mockSummary.mockResolvedValue({ data: { data: null } })
    mockApplications.mockResolvedValue(emptyRows)
    mockPremium.mockResolvedValue(emptyRows)
    mockClaims.mockResolvedValue(emptyRows)
    renderPage()
    expect(await screen.findByText(/no report data available/i)).toBeInTheDocument()
  })
})
