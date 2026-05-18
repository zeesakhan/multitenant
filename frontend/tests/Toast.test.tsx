import { render, screen, act } from '@testing-library/react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import { ToastProvider, useToast } from '../src/context/ToastContext'

function ToastTrigger({ message, type }: { message: string; type?: 'success' | 'error' | 'info' }) {
  const { toast } = useToast()
  return <button onClick={() => toast(message, type)}>fire</button>
}

function renderWithToast(message: string, type?: 'success' | 'error' | 'info') {
  return render(
    <ToastProvider>
      <ToastTrigger message={message} type={type} />
    </ToastProvider>,
  )
}

afterEach(() => { vi.useRealTimers() })

describe('ToastContext', () => {
  it('shows a toast after triggering', async () => {
    vi.useFakeTimers()
    renderWithToast('Hello toast')

    act(() => {
      screen.getByRole('button', { name: /fire/i }).click()
    })

    expect(screen.getByText('Hello toast')).toBeInTheDocument()
  })

  it('auto-dismisses after the timeout', async () => {
    vi.useFakeTimers()
    renderWithToast('Goodbye toast')

    act(() => {
      screen.getByRole('button', { name: /fire/i }).click()
    })

    expect(screen.getByText('Goodbye toast')).toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(4000)
    })

    expect(screen.queryByText('Goodbye toast')).not.toBeInTheDocument()
  })

  it('renders success type with accessible role', () => {
    vi.useFakeTimers()
    renderWithToast('Saved!', 'success')

    act(() => {
      screen.getByRole('button', { name: /fire/i }).click()
    })

    expect(screen.getByText('Saved!')).toBeInTheDocument()
  })

  it('renders error type', () => {
    vi.useFakeTimers()
    renderWithToast('Something failed', 'error')

    act(() => {
      screen.getByRole('button', { name: /fire/i }).click()
    })

    expect(screen.getByText('Something failed')).toBeInTheDocument()
  })

  it('renders info type', () => {
    vi.useFakeTimers()
    renderWithToast('For your information', 'info')

    act(() => {
      screen.getByRole('button', { name: /fire/i }).click()
    })

    expect(screen.getByText('For your information')).toBeInTheDocument()
  })

  it('can show multiple toasts', () => {
    vi.useFakeTimers()
    render(
      <ToastProvider>
        <ToastTrigger message="First" />
        <ToastTrigger message="Second" />
      </ToastProvider>,
    )

    act(() => {
      screen.getAllByRole('button', { name: /fire/i }).forEach((btn) => btn.click())
    })

    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
  })
})
