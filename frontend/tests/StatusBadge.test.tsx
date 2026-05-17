import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from '../src/components/StatusBadge'

describe('StatusBadge', () => {
  it('renders lowercase status text', () => {
    render(<StatusBadge status="ACTIVE" />)
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('applies green class for active', () => {
    const { container } = render(<StatusBadge status="active" />)
    expect(container.firstChild).toHaveClass('badge-green')
  })

  it('applies red class for rejected', () => {
    const { container } = render(<StatusBadge status="rejected" />)
    expect(container.firstChild).toHaveClass('badge-red')
  })

  it('applies red class for suspended', () => {
    const { container } = render(<StatusBadge status="SUSPENDED" />)
    expect(container.firstChild).toHaveClass('badge-red')
  })

  it('applies yellow class for pending', () => {
    const { container } = render(<StatusBadge status="pending" />)
    expect(container.firstChild).toHaveClass('badge-yellow')
  })

  it('applies blue class for submitted', () => {
    const { container } = render(<StatusBadge status="submitted" />)
    expect(container.firstChild).toHaveClass('badge-blue')
  })

  it('applies gray class for draft', () => {
    const { container } = render(<StatusBadge status="draft" />)
    expect(container.firstChild).toHaveClass('badge-gray')
  })

  it('falls back to gray for unknown status', () => {
    const { container } = render(<StatusBadge status="unknown_xyz" />)
    expect(container.firstChild).toHaveClass('badge-gray')
  })
})
