import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockForgotPassword } = vi.hoisted(() => ({ mockForgotPassword: vi.fn() }))

vi.mock('../src/services/api', () => ({
  default: {},
  authApi: { forgotPassword: mockForgotPassword },
}))

import ForgotPasswordPage from '../src/pages/ForgotPasswordPage'

function renderPage() {
  return render(
    <MemoryRouter><ForgotPasswordPage /></MemoryRouter>,
  )
}

describe('ForgotPasswordPage', () => {
  beforeEach(() => mockForgotPassword.mockReset())

  it('renders heading and email input', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/you@company\.com/i)).toBeInTheDocument()
  })

  it('renders send reset link button', () => {
    renderPage()
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument()
  })

  it('shows check your inbox after successful submit', async () => {
    mockForgotPassword.mockResolvedValue({ data: {} })
    renderPage()
    fireEvent.change(screen.getByPlaceholderText(/you@company\.com/i), {
      target: { value: 'user@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    expect(await screen.findByText(/check your inbox/i)).toBeInTheDocument()
  })

  it('has a back to sign in link', () => {
    renderPage()
    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument()
  })
})
