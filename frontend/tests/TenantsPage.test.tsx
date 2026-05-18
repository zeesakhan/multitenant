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
  tenantsApi: { list: mockList, create: mockCreate, get: vi.fn(), update: vi.fn() },
}))

vi.mock('../src/store/authStore', () => ({
  useAuth: () => ({ user: { user_type: 'super_admin' } }),
}))

vi.mock('../src/context/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

import TenantsPage from '../src/pages/TenantsPage'

const emptyList = { data: { data: [] } }
const tenantList = {
  data: {
    data: [
      {
        id: 't1',
        name: 'Acme Corp',
        code: 'ACME',
        status: 'active',
        currency: 'USD',
        timezone: 'UTC',
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
  },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><TenantsPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('TenantsPage', () => {
  beforeEach(() => { mockList.mockReset(); mockCreate.mockReset() })

  it('shows empty state when no tenants', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    expect(await screen.findByText('No tenants found')).toBeInTheDocument()
  })

  it('renders a tenant row', async () => {
    mockList.mockResolvedValue(tenantList)
    renderPage()
    expect(await screen.findByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('ACME')).toBeInTheDocument()
  })

  it('opens add-tenant modal', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    await screen.findByText('No tenants found')
    fireEvent.click(screen.getByRole('button', { name: /add tenant/i }))
    expect(await screen.findByRole('heading', { name: /add new tenant/i })).toBeInTheDocument()
  })

  it('shows currency column', async () => {
    mockList.mockResolvedValue(tenantList)
    renderPage()
    await screen.findByText('Acme Corp')
    expect(screen.getByText('USD')).toBeInTheDocument()
  })
})
