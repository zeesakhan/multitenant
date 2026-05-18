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
  applicationsApi: {
    list: mockList,
    create: mockCreate,
    get: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    issue: vi.fn(),
    addItem: vi.fn(),
    removeItem: vi.fn(),
  },
  productsApi: { list: vi.fn().mockResolvedValue({ data: { data: [] } }) },
  plansApi: { list: vi.fn().mockResolvedValue({ data: { data: [] } }) },
  membersApi: { add: vi.fn(), remove: vi.fn() },
}))

vi.mock('../src/context/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

import ApplicationsPage from '../src/pages/ApplicationsPage'

const emptyList = { data: { data: [] } }
const appList = {
  data: {
    data: [
      {
        id: 'app1',
        application_number: 'APP-001',
        customer_name: 'Bob Smith',
        customer_email: 'bob@example.com',
        status: 'draft',
        total_premium: '350.00',
        member_count: 1,
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
        <ApplicationsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ApplicationsPage', () => {
  beforeEach(() => {
    mockList.mockReset()
    mockCreate.mockReset()
  })

  it('shows empty state when no applications', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    expect(await screen.findByText(/no applications yet/i)).toBeInTheDocument()
  })

  it('renders application row with number and customer', async () => {
    mockList.mockResolvedValue(appList)
    renderPage()
    expect(await screen.findByText('Bob Smith')).toBeInTheDocument()
    expect(screen.getByText('APP-001')).toBeInTheDocument()
  })

  it('opens new-application modal with title', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    await screen.findByText(/no applications yet/i)
    fireEvent.click(screen.getAllByRole('button', { name: /new application/i })[0])
    expect(await screen.findByRole('heading', { name: 'New Application' })).toBeInTheDocument()
  })

  it('shows "View / Act" link for each application', async () => {
    mockList.mockResolvedValue(appList)
    renderPage()
    expect(await screen.findByText(/view \/ act/i)).toBeInTheDocument()
  })
})
