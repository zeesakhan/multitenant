import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }))

vi.mock('../src/services/api', () => ({
  default: { get: mockGet },
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

function clickContinue() {
  fireEvent.click(screen.getByRole('button', { name: /continue/i }))
}

describe('LoginPage', () => {
  beforeEach(() => mockGet.mockReset())

  it('renders the tenant lookup step by default', () => {
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(screen.getByText('Find your organisation')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('e.g. TESTCO')).toBeInTheDocument()
  })

  it('disables the continue button while a lookup is in progress', async () => {
    // Hang the request so the loading state is observable
    let resolve: (v: unknown) => void
    mockGet.mockReturnValue(new Promise(r => { resolve = r }))
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    const btn = screen.getByRole('button', { name: /continue/i })
    expect(btn).not.toBeDisabled()
    clickContinue()
    expect(await screen.findByText(/looking up/i)).toBeInTheDocument()
    expect(btn).toBeDisabled()
    // cleanup: resolve the hanging promise
    resolve!({ data: { data: { id: 'x', name: 'X' } } })
  })

  it('advances to the credentials step after a successful tenant lookup', async () => {
    mockGet.mockResolvedValue({
      data: { data: { id: 'tenant-abc', name: 'Acme Corp' } },
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    clickContinue()
    expect(await screen.findByText('Acme Corp')).toBeInTheDocument()
    // heading distinguishes from the submit button which also says "Sign in"
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows "change organisation" link on credentials step', async () => {
    mockGet.mockResolvedValue({
      data: { data: { id: 'tid', name: 'Test Org' } },
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    clickContinue()
    expect(await screen.findByText(/change organisation/i)).toBeInTheDocument()
  })

  it('goes back to the tenant step when "change organisation" is clicked', async () => {
    mockGet.mockResolvedValue({
      data: { data: { id: 'tid', name: 'Test Org' } },
    })
    render(<MemoryRouter><LoginPage /></MemoryRouter>)
    clickContinue()
    fireEvent.click(await screen.findByText(/change organisation/i))
    expect(screen.getByText('Find your organisation')).toBeInTheDocument()
  })
})
