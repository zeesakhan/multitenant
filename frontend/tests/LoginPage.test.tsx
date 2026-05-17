import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/services/api', () => ({
  default: { get: vi.fn() },
  authApi: { login: vi.fn(), me: vi.fn() },
}))

vi.mock('../src/store/authStore', () => ({
  setAuth: vi.fn(),
}))

vi.mock('react-router-dom', async (importOriginal) => {
  const mod = await importOriginal<typeof import('react-router-dom')>()
  return { ...mod, useNavigate: () => vi.fn() }
})

import LoginPage from '../src/pages/LoginPage'
import api from '../src/services/api'

describe('LoginPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the tenant lookup step by default', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByText('Find your organisation')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('e.g. TESTCO')).toBeInTheDocument()
  })

  it('shows an error when the tenant code is not found', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('Not found'))
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() =>
      expect(screen.getByText(/tenant not found/i)).toBeInTheDocument()
    )
  })

  it('advances to the credentials step after a successful tenant lookup', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { data: { id: 'tenant-abc', name: 'Acme Corp' } },
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument()
      expect(screen.getByText('Sign in')).toBeInTheDocument()
    })
  })

  it('shows "change organisation" link on credentials step', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { data: { id: 'tid', name: 'Test Org' } },
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => expect(screen.getByText(/change organisation/i)).toBeInTheDocument())
  })

  it('goes back to tenant step when "change organisation" is clicked', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { data: { id: 'tid', name: 'Test Org' } },
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /continue/i }))
    await waitFor(() => screen.getByText(/change organisation/i))
    fireEvent.click(screen.getByText(/change organisation/i))
    expect(screen.getByText('Find your organisation')).toBeInTheDocument()
  })
})
