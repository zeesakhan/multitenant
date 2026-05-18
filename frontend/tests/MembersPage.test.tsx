import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockListAll } = vi.hoisted(() => ({ mockListAll: vi.fn() }))

vi.mock('../src/services/api', () => ({
  default: {},
  membersApi: { listAll: mockListAll },
}))

import MembersPage from '../src/pages/MembersPage'

const emptyResponse = { data: [], pagination: { total: 0, page: 1, per_page: 20, total_pages: 1 } }
const memberResponse = {
  data: [
    {
      id: 'm1',
      first_name: 'Alice',
      last_name: 'Smith',
      date_of_birth: '1990-05-15',
      relationship: 'self',
      gender: 'F',
      email: 'alice@example.com',
      phone: null,
      status: 'active',
    },
  ],
  pagination: { total: 1, page: 1, per_page: 20, total_pages: 1 },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><MembersPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('MembersPage', () => {
  beforeEach(() => mockListAll.mockReset())

  it('renders page header', async () => {
    mockListAll.mockResolvedValue({ data: emptyResponse })
    renderPage()
    expect(await screen.findByText('Members')).toBeInTheDocument()
  })

  it('shows a member row when data is returned', async () => {
    mockListAll.mockResolvedValue({ data: memberResponse })
    renderPage()
    expect(await screen.findByText('Alice Smith')).toBeInTheDocument()
    expect(screen.getByText('self')).toBeInTheDocument()
  })

  it('shows total member count in subtitle', async () => {
    mockListAll.mockResolvedValue({ data: memberResponse })
    renderPage()
    expect(await screen.findByText(/1 members/)).toBeInTheDocument()
  })
})
