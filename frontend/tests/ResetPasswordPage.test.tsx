import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockResetPassword } = vi.hoisted(() => ({ mockResetPassword: vi.fn() }))

vi.mock('../src/services/api', () => ({
  default: {},
  authApi: { resetPassword: mockResetPassword },
}))

import ResetPasswordPage from '../src/pages/ResetPasswordPage'

function renderWithToken(token?: string) {
  const url = token ? `/reset-password?token=${token}` : '/reset-password'
  return render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ResetPasswordPage', () => {
  beforeEach(() => mockResetPassword.mockReset())

  it('shows error when no token in URL', () => {
    renderWithToken()
    expect(screen.getByText(/invalid or missing reset token/i)).toBeInTheDocument()
  })

  it('renders set new password form when token present', () => {
    renderWithToken('abc123')
    expect(screen.getByRole('heading', { name: /set new password/i })).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/min 8 characters/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/repeat password/i)).toBeInTheDocument()
  })

  it('shows error when passwords do not match', async () => {
    renderWithToken('abc123')
    fireEvent.change(screen.getByPlaceholderText(/min 8 characters/i), { target: { value: 'password1' } })
    fireEvent.change(screen.getByPlaceholderText(/repeat password/i), { target: { value: 'password2' } })
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }))
    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument()
  })

  it('calls resetPassword and redirects on success', async () => {
    mockResetPassword.mockResolvedValue({ data: {} })
    renderWithToken('valid-token')
    fireEvent.change(screen.getByPlaceholderText(/min 8 characters/i), { target: { value: 'newpass1' } })
    fireEvent.change(screen.getByPlaceholderText(/repeat password/i), { target: { value: 'newpass1' } })
    fireEvent.click(screen.getByRole('button', { name: /set new password/i }))
    expect(await screen.findByText('Login page')).toBeInTheDocument()
    expect(mockResetPassword).toHaveBeenCalledWith('valid-token', 'newpass1')
  })

})
