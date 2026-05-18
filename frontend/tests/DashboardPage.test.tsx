import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockStats, mockHealth } = vi.hoisted(() => ({
  mockStats: vi.fn(),
  mockHealth: vi.fn(),
}))

vi.mock('../src/services/api', () => ({
  default: {},
  dashboardApi: { stats: mockStats },
  healthApi: { check: mockHealth },
}))

vi.mock('../src/store/authStore', () => ({
  useAuth: () => ({ user: { first_name: 'Alice', user_type: 'tenant_admin' } }),
}))

import DashboardPage from '../src/pages/DashboardPage'

const statsResponse = {
  data: {
    data: {
      policies: { active: 5, total: 10, monthly_premium: 2500 },
      applications: { total: 8, by_status: { submitted: 3, approved: 2, issued: 1, rejected: 1, draft: 1, cancelled: 0 } },
      payments: { total: 12, total_collected: 9800 },
      users: { total: 4 },
      recent_applications: [
        { id: 'a1', customer_name: 'Bob Jones', application_number: 'APP-001', status: 'submitted' },
      ],
      recent_payments: [
        { id: 'p1', amount: 400, method: 'bank_transfer', paid_at: '2026-02-01T10:00:00Z' },
      ],
    },
  },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><DashboardPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  beforeEach(() => { mockStats.mockReset(); mockHealth.mockReset() })

  it('renders page header', async () => {
    mockStats.mockResolvedValue(statsResponse)
    mockHealth.mockResolvedValue({ data: { status: 'ok' } })
    renderPage()
    expect(await screen.findByText('Dashboard')).toBeInTheDocument()
  })

  it('shows active policy count', async () => {
    mockStats.mockResolvedValue(statsResponse)
    mockHealth.mockResolvedValue({ data: { status: 'ok' } })
    renderPage()
    expect(await screen.findByText('5')).toBeInTheDocument()
    expect(screen.getByText('Active Policies')).toBeInTheDocument()
  })

  it('shows recent application in list', async () => {
    mockStats.mockResolvedValue(statsResponse)
    mockHealth.mockResolvedValue({ data: { status: 'ok' } })
    renderPage()
    expect(await screen.findByText('Bob Jones')).toBeInTheDocument()
    expect(screen.getByText('APP-001')).toBeInTheDocument()
  })

  it('shows recent payment amount', async () => {
    mockStats.mockResolvedValue(statsResponse)
    mockHealth.mockResolvedValue({ data: { status: 'ok' } })
    renderPage()
    expect(await screen.findByText('$400.00')).toBeInTheDocument()
    expect(screen.getByText('Bank Transfer')).toBeInTheDocument()
  })

  it('shows empty state message when no stats', async () => {
    mockStats.mockResolvedValue({ data: { data: null } })
    mockHealth.mockRejectedValue(new Error('offline'))
    renderPage()
    expect(await screen.findByText(/unable to load dashboard stats/i)).toBeInTheDocument()
  })
})
