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
  usersApi: { list: mockList, create: mockCreate, update: vi.fn(), delete: vi.fn() },
}))

vi.mock('../src/context/ToastContext', () => ({
  useToast: () => ({ toast: vi.fn() }),
}))

import UsersPage from '../src/pages/UsersPage'

const emptyList = { data: { data: [] } }
const userList = {
  data: {
    data: [
      {
        id: 'u1',
        first_name: 'Jane',
        last_name: 'Doe',
        email: 'jane@example.com',
        user_type: 'agent',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
  },
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter><UsersPage /></MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('UsersPage', () => {
  beforeEach(() => { mockList.mockReset(); mockCreate.mockReset() })

  it('shows empty state when no users', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    expect(await screen.findByText('No users found')).toBeInTheDocument()
  })

  it('renders a user row', async () => {
    mockList.mockResolvedValue(userList)
    renderPage()
    expect(await screen.findByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByText('jane@example.com')).toBeInTheDocument()
  })

  it('opens add-user modal', async () => {
    mockList.mockResolvedValue(emptyList)
    renderPage()
    await screen.findByText('No users found')
    fireEvent.click(screen.getByRole('button', { name: /add user/i }))
    expect(await screen.findByRole('heading', { name: /add new user/i })).toBeInTheDocument()
  })

  it('shows user type badge', async () => {
    mockList.mockResolvedValue(userList)
    renderPage()
    await screen.findByText('Jane Doe')
    expect(screen.getByText('agent')).toBeInTheDocument()
  })
})
